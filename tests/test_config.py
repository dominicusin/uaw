"""
UAW Config Module Tests

Comprehensive tests for the configuration management system including:
- ConfigManager
- IntegrationConfig
- SecurityConfig
- AutomationConfig
"""

import unittest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from uaw.config.config_manager import ConfigManager, ConfigValidationError
from uaw.config.integration_config import (
    IntegrationConfig,
    IntegrationAuthType,
    IntegrationSettings,
    RateLimitConfig,
)
from uaw.config.security_config import (
    SecurityConfig,
    PermissionLevel,
    BlockedAction,
    AuditSettings,
    SessionConfig,
)
from uaw.config.automation_config import (
    AutomationConfig,
    TriggerConfig,
    WebhookConfig,
    ExecutionSettings,
    RetryPolicy,
)


class TestConfigManager(unittest.TestCase):
    """Tests for ConfigManager class"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.json")
        self.yaml_path = os.path.join(self.temp_dir, "test_config.yaml")
        self.config_manager = ConfigManager(config_dir=self.temp_dir)

    def tearDown(self):
        # Clean up temp files
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_config_manager_initialization(self):
        """Test ConfigManager initialization"""
        self.assertEqual(self.config_manager.config_dir, self.temp_dir)
        self.assertIsNotNone(self.config_manager._configs)

    def test_save_and_load_json_config(self):
        """Test saving and loading JSON configuration"""
        config = {
            "integration": {
                "github": {
                    "auth_type": "oauth2",
                    "enabled": True,
                    "rate_limit": {"requests": 5000, "period": "hour"}
                }
            }
        }
        
        self.config_manager.save_config(config, self.config_path)
        loaded = self.config_manager.load_config(self.config_path)
        
        self.assertEqual(loaded, config)

    def test_save_and_load_yaml_config(self):
        """Test saving and loading YAML configuration"""
        config = {
            "integration": {
                "github": {
                    "auth_type": "oauth2",
                    "enabled": True
                }
            }
        }
        
        self.config_manager.save_config(config, self.yaml_path, format="yaml")
        loaded = self.config_manager.load_config(self.yaml_path, format="yaml")
        
        self.assertEqual(loaded, config)

    def test_load_nonexistent_config(self):
        """Test loading a non-existent configuration file"""
        with self.assertRaises(FileNotFoundError):
            self.config_manager.load_config("/nonexistent/path/config.json")

    def test_load_invalid_json(self):
        """Test loading an invalid JSON file"""
        invalid_json_path = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_json_path, 'w') as f:
            f.write('{"invalid": json}')
        
        with self.assertRaises(json.JSONDecodeError):
            self.config_manager.load_config(invalid_json_path)

    def test_validate_config_success(self):
        """Test successful configuration validation"""
        config = {
            "integration": {
                "github": {"enabled": True}
            },
            "security": {
                "default_permission": "L2"
            }
        }
        
        # Should not raise an exception
        self.config_manager.validate_config(config, required_keys=["integration", "security"])

    def test_validate_config_missing_keys(self):
        """Test validation failure for missing required keys"""
        config = {
            "integration": {"github": {"enabled": True}}
        }
        
        with self.assertRaises(ConfigValidationError):
            self.config_manager.validate_config(config, required_keys=["integration", "security"])

    def test_validate_config_wrong_type(self):
        """Test validation failure for wrong data types"""
        config = {
            "integration": {
                "github": {"enabled": "yes"}  # Should be boolean
            }
        }
        
        with self.assertRaises(ConfigValidationError):
            self.config_manager.validate_config(config, schema={
                "integration": {
                    "github": {"enabled": bool}
                }
            })

    def test_get_config_by_type(self):
        """Test getting configuration by type"""
        integration_config = IntegrationConfig(
            service_name="github",
            auth_type=IntegrationAuthType.OAUTH2,
            enabled=True
        )
        
        self.config_manager._configs["integration"] = integration_config.to_dict()
        
        retrieved = self.config_manager.get_config("integration", IntegrationConfig)
        self.assertIsInstance(retrieved, IntegrationConfig)
        self.assertEqual(retrieved.service_name, "github")

    def test_get_config_not_found(self):
        """Test getting a non-existent configuration"""
        with self.assertRaises(KeyError):
            self.config_manager.get_config("nonexistent", IntegrationConfig)

    def test_merge_configs(self):
        """Test merging multiple configurations"""
        config1 = {"integration": {"github": {"enabled": True}}}
        config2 = {"security": {"level": "L2"}}
        
        merged = self.config_manager.merge_configs(config1, config2)
        
        self.assertIn("integration", merged)
        self.assertIn("security", merged)
        self.assertEqual(merged["integration"]["github"]["enabled"], True)
        self.assertEqual(merged["security"]["level"], "L2")

    def test_get_environment_config(self):
        """Test getting configuration from environment variables"""
        with patch.dict(os.environ, {"UAW_GITHUB_ENABLED": "true", "UAW_GITHUB_TOKEN": "test_token"}):
            config = self.config_manager.get_environment_config(
                prefix="UAW_",
                mapping={"GITHUB_ENABLED": ("integration", "github", "enabled", bool)},
                expected_type={"integration": {"github": {"enabled": bool, "token": str}}}
            )
            
            self.assertIn("integration", config)
            self.assertIn("github", config["integration"])
            self.assertTrue(config["integration"]["github"]["enabled"])

    def test_list_configs(self):
        """Test listing all loaded configurations"""
        self.config_manager._configs["test1"] = {"key": "value1"}
        self.config_manager._configs["test2"] = {"key": "value2"}
        
        configs = self.config_manager.list_configs()
        
        self.assertEqual(len(configs), 2)
        self.assertIn("test1", configs)
        self.assertIn("test2", configs)

    def test_reset_configs(self):
        """Test resetting all configurations"""
        self.config_manager._configs["test"] = {"key": "value"}
        self.config_manager.reset_configs()
        
        self.assertEqual(len(self.config_manager._configs), 0)


class TestIntegrationConfig(unittest.TestCase):
    """Tests for IntegrationConfig class"""

    def test_integration_config_creation(self):
        """Test creating an integration configuration"""
        config = IntegrationConfig(
            service_name="github",
            auth_type=IntegrationAuthType.OAUTH2,
            enabled=True,
            api_key="test_key",
            base_url="https://api.github.com",
            rate_limit=RateLimitConfig(requests=5000, period="hour"),
            settings=IntegrationSettings(
                timeout=30,
                retry_attempts=3,
                retry_delay=1.0
            )
        )
        
        self.assertEqual(config.service_name, "github")
        self.assertEqual(config.auth_type, IntegrationAuthType.OAUTH2)
        self.assertTrue(config.enabled)
        self.assertEqual(config.api_key, "test_key")
        self.assertEqual(config.base_url, "https://api.github.com")
        self.assertEqual(config.rate_limit.requests, 5000)
        self.assertEqual(config.settings.timeout, 30)

    def test_integration_config_to_dict(self):
        """Test integration config serialization"""
        config = IntegrationConfig(
            service_name="github",
            auth_type=IntegrationAuthType.OAUTH2,
            enabled=True
        )
        
        config_dict = config.to_dict()
        
        self.assertIn("service_name", config_dict)
        self.assertIn("auth_type", config_dict)
        self.assertIn("enabled", config_dict)
        self.assertEqual(config_dict["service_name"], "github")

    def test_integration_config_from_dict(self):
        """Test integration config deserialization"""
        config_dict = {
            "service_name": "github",
            "auth_type": "oauth2",
            "enabled": True,
            "rate_limit": {"requests": 5000, "period": "hour"}
        }
        
        config = IntegrationConfig.from_dict(config_dict)
        
        self.assertEqual(config.service_name, "github")
        self.assertEqual(config.auth_type, IntegrationAuthType.OAUTH2)
        self.assertTrue(config.enabled)
        self.assertEqual(config.rate_limit.requests, 5000)

    def test_rate_limit_config(self):
        """Test rate limit configuration"""
        rate_limit = RateLimitConfig(
            requests=100,
            period="minute",
            burst_requests=200,
            burst_period="minute"
        )
        
        self.assertEqual(rate_limit.requests, 100)
        self.assertEqual(rate_limit.period, "minute")
        self.assertEqual(rate_limit.burst_requests, 200)

    def test_integration_settings(self):
        """Test integration settings"""
        settings = IntegrationSettings(
            timeout=60,
            retry_attempts=5,
            retry_delay=2.0,
            retry_backoff=1.5,
            max_connections=100,
            connection_timeout=10
        )
        
        self.assertEqual(settings.timeout, 60)
        self.assertEqual(settings.retry_attempts, 5)
        self.assertEqual(settings.retry_delay, 2.0)
        self.assertEqual(settings.retry_backoff, 1.5)

    def test_auth_types(self):
        """Test all authentication types"""
        self.assertEqual(IntegrationAuthType.OAUTH2.value, "oauth2")
        self.assertEqual(IntegrationAuthType.API_KEY.value, "api_key")
        self.assertEqual(IntegrationAuthType.BASIC.value, "basic")
        self.assertEqual(IntegrationAuthType.BEARER.value, "bearer")
        self.assertEqual(IntegrationAuthType.NONE.value, "none")

    def test_default_integration_config(self):
        """Test default integration configuration"""
        config = IntegrationConfig()
        
        self.assertEqual(config.service_name, "")
        self.assertEqual(config.auth_type, IntegrationAuthType.NONE)
        self.assertFalse(config.enabled)
        self.assertIsNone(config.api_key)


class TestSecurityConfig(unittest.TestCase):
    """Tests for SecurityConfig class"""

    def test_security_config_creation(self):
        """Test creating a security configuration"""
        config = SecurityConfig(
            default_permission=PermissionLevel.L2,
            blocked_actions=[
                BlockedAction(
                    action_type="production_deploy",
                    reason="Requires explicit approval",
                    required_permission=PermissionLevel.L4
                )
            ],
            audit_settings=AuditSettings(
                enabled=True,
                log_file="/var/log/uaw/audit.log",
                max_file_size=10485760,  # 10MB
                max_backup_files=5
            ),
            session_config=SessionConfig(
                session_timeout=3600,  # 1 hour
                max_sessions_per_user=10,
                session_encryption_key="test_key"
            ),
            token_encryption_enabled=True,
            ip_whitelist=["192.168.1.0/24", "10.0.0.0/8"],
            require_2fa_for_l4=True
        )
        
        self.assertEqual(config.default_permission, PermissionLevel.L2)
        self.assertEqual(len(config.blocked_actions), 1)
        self.assertTrue(config.audit_settings.enabled)
        self.assertEqual(config.session_config.session_timeout, 3600)
        self.assertTrue(config.token_encryption_enabled)
        self.assertIn("192.168.1.0/24", config.ip_whitelist)

    def test_security_config_to_dict(self):
        """Test security config serialization"""
        config = SecurityConfig(
            default_permission=PermissionLevel.L2,
            token_encryption_enabled=True
        )
        
        config_dict = config.to_dict()
        
        self.assertIn("default_permission", config_dict)
        self.assertIn("token_encryption_enabled", config_dict)
        self.assertEqual(config_dict["default_permission"], "L2")

    def test_security_config_from_dict(self):
        """Test security config deserialization"""
        config_dict = {
            "default_permission": "L2",
            "token_encryption_enabled": True,
            "require_2fa_for_l4": True
        }
        
        config = SecurityConfig.from_dict(config_dict)
        
        self.assertEqual(config.default_permission, PermissionLevel.L2)
        self.assertTrue(config.token_encryption_enabled)
        self.assertTrue(config.require_2fa_for_l4)

    def test_permission_levels(self):
        """Test all permission levels"""
        self.assertEqual(PermissionLevel.L0.value, "L0")
        self.assertEqual(PermissionLevel.L1.value, "L1")
        self.assertEqual(PermissionLevel.L2.value, "L2")
        self.assertEqual(PermissionLevel.L3.value, "L3")
        self.assertEqual(PermissionLevel.L4.value, "L4")

    def test_permission_level_comparison(self):
        """Test permission level comparison"""
        self.assertTrue(PermissionLevel.L4 > PermissionLevel.L3)
        self.assertTrue(PermissionLevel.L2 < PermissionLevel.L3)
        self.assertTrue(PermissionLevel.L0 <= PermissionLevel.L1)
        self.assertTrue(PermissionLevel.L4 >= PermissionLevel.L4)

    def test_blocked_action(self):
        """Test blocked action configuration"""
        action = BlockedAction(
            action_type="delete_data",
            reason="Irreversible operation",
            required_permission=PermissionLevel.L4,
            allowed_roles=["admin", "superadmin"]
        )
        
        self.assertEqual(action.action_type, "delete_data")
        self.assertEqual(action.reason, "Irreversible operation")
        self.assertEqual(action.required_permission, PermissionLevel.L4)
        self.assertIn("admin", action.allowed_roles)

    def test_audit_settings(self):
        """Test audit settings"""
        settings = AuditSettings(
            enabled=True,
            log_file="/var/log/uaw/audit.log",
            max_file_size=10485760,
            max_backup_files=5,
            log_level="INFO",
            include_timestamp=True,
            include_user_info=True
        )
        
        self.assertTrue(settings.enabled)
        self.assertEqual(settings.log_file, "/var/log/uaw/audit.log")
        self.assertEqual(settings.max_file_size, 10485760)
        self.assertEqual(settings.log_level, "INFO")

    def test_session_config(self):
        """Test session configuration"""
        config = SessionConfig(
            session_timeout=3600,
            max_sessions_per_user=10,
            session_encryption_key="test_encryption_key",
            session_prefix="uaw_session_",
            cookie_name="uaw_session_id",
            cookie_secure=True,
            cookie_httponly=True
        )
        
        self.assertEqual(config.session_timeout, 3600)
        self.assertEqual(config.max_sessions_per_user, 10)
        self.assertEqual(config.session_encryption_key, "test_encryption_key")
        self.assertTrue(config.cookie_secure)

    def test_default_security_config(self):
        """Test default security configuration"""
        config = SecurityConfig()
        
        self.assertEqual(config.default_permission, PermissionLevel.L2)
        self.assertFalse(config.token_encryption_enabled)
        self.assertEqual(len(config.blocked_actions), 0)


class TestAutomationConfig(unittest.TestCase):
    """Tests for AutomationConfig class"""

    def test_automation_config_creation(self):
        """Test creating an automation configuration"""
        config = AutomationConfig(
            enabled=True,
            webhooks=[
                WebhookConfig(
                    name="github_webhook",
                    url="https://api.github.com/webhooks",
                    secret="test_secret",
                    events=["issues", "pull_requests", "push"],
                    enabled=True,
                    rate_limit=100
                )
            ],
            triggers=[
                TriggerConfig(
                    name="daily_backup",
                    trigger_type="scheduled",
                    schedule="0 2 * * *",  # Daily at 2 AM
                    enabled=True
                )
            ],
            execution_settings=ExecutionSettings(
                max_concurrent_tasks=10,
                task_timeout=3600,
                queue_size=1000,
                retry_policy=RetryPolicy(
                    max_attempts=3,
                    initial_delay=1.0,
                    max_delay=60.0,
                    backoff_factor=2.0,
                    retryable_errors=["rate_limit", "timeout", "connection_error"]
                )
            ),
            poll_interval=60,
            max_poll_attempts=5
        )
        
        self.assertTrue(config.enabled)
        self.assertEqual(len(config.webhooks), 1)
        self.assertEqual(len(config.triggers), 1)
        self.assertEqual(config.execution_settings.max_concurrent_tasks, 10)
        self.assertEqual(config.poll_interval, 60)

    def test_automation_config_to_dict(self):
        """Test automation config serialization"""
        config = AutomationConfig(
            enabled=True,
            poll_interval=60
        )
        
        config_dict = config.to_dict()
        
        self.assertIn("enabled", config_dict)
        self.assertIn("poll_interval", config_dict)
        self.assertTrue(config_dict["enabled"])

    def test_automation_config_from_dict(self):
        """Test automation config deserialization"""
        config_dict = {
            "enabled": True,
            "poll_interval": 60,
            "max_poll_attempts": 5
        }
        
        config = AutomationConfig.from_dict(config_dict)
        
        self.assertTrue(config.enabled)
        self.assertEqual(config.poll_interval, 60)
        self.assertEqual(config.max_poll_attempts, 5)

    def test_webhook_config(self):
        """Test webhook configuration"""
        webhook = WebhookConfig(
            name="github_webhook",
            url="https://api.github.com/webhooks",
            secret="test_secret",
            events=["issues", "pull_requests", "push"],
            enabled=True,
            rate_limit=100,
            headers={"X-GitHub-Event": "true"},
            verify_ssl=True
        )
        
        self.assertEqual(webhook.name, "github_webhook")
        self.assertEqual(webhook.url, "https://api.github.com/webhooks")
        self.assertEqual(webhook.secret, "test_secret")
        self.assertIn("issues", webhook.events)
        self.assertTrue(webhook.enabled)
        self.assertEqual(webhook.rate_limit, 100)

    def test_trigger_config(self):
        """Test trigger configuration"""
        trigger = TriggerConfig(
            name="hourly_sync",
            trigger_type="scheduled",
            schedule="0 * * * *",  # Every hour
            enabled=True,
            conditions={"service": "github", "event": "push"},
            payload_template={"action": "sync", "service": "{{service}}"}
        )
        
        self.assertEqual(trigger.name, "hourly_sync")
        self.assertEqual(trigger.trigger_type, "scheduled")
        self.assertEqual(trigger.schedule, "0 * * * *")
        self.assertTrue(trigger.enabled)
        self.assertEqual(trigger.conditions["service"], "github")

    def test_execution_settings(self):
        """Test execution settings"""
        settings = ExecutionSettings(
            max_concurrent_tasks=20,
            task_timeout=7200,
            queue_size=2000,
            retry_policy=RetryPolicy(
                max_attempts=5,
                initial_delay=0.5,
                max_delay=120.0,
                backoff_factor=1.5,
                retryable_errors=["rate_limit", "timeout"]
            ),
            worker_count=4,
            batch_size=100
        )
        
        self.assertEqual(settings.max_concurrent_tasks, 20)
        self.assertEqual(settings.task_timeout, 7200)
        self.assertEqual(settings.queue_size, 2000)
        self.assertEqual(settings.retry_policy.max_attempts, 5)
        self.assertEqual(settings.worker_count, 4)

    def test_retry_policy(self):
        """Test retry policy"""
        policy = RetryPolicy(
            max_attempts=3,
            initial_delay=1.0,
            max_delay=60.0,
            backoff_factor=2.0,
            retryable_errors=["rate_limit", "timeout", "connection_error"],
            non_retryable_errors=["permission_error", "validation_error"]
        )
        
        self.assertEqual(policy.max_attempts, 3)
        self.assertEqual(policy.initial_delay, 1.0)
        self.assertEqual(policy.max_delay, 60.0)
        self.assertEqual(policy.backoff_factor, 2.0)
        self.assertIn("rate_limit", policy.retryable_errors)
        self.assertIn("permission_error", policy.non_retryable_errors)

    def test_default_automation_config(self):
        """Test default automation configuration"""
        config = AutomationConfig()
        
        self.assertFalse(config.enabled)
        self.assertEqual(len(config.webhooks), 0)
        self.assertEqual(len(config.triggers), 0)
        self.assertEqual(config.poll_interval, 60)


class TestConfigIntegration(unittest.TestCase):
    """Integration tests for configuration components working together"""

    def test_full_config_workflow(self):
        """Test a complete configuration workflow"""
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create config manager
            config_manager = ConfigManager(config_dir=temp_dir)
            
            # Create integration config
            integration_config = IntegrationConfig(
                service_name="github",
                auth_type=IntegrationAuthType.OAUTH2,
                enabled=True,
                rate_limit=RateLimitConfig(requests=5000, period="hour")
            )
            
            # Create security config
            security_config = SecurityConfig(
                default_permission=PermissionLevel.L2,
                token_encryption_enabled=True
            )
            
            # Create automation config
            automation_config = AutomationConfig(
                enabled=True,
                poll_interval=60
            )
            
            # Save configs
            integration_path = os.path.join(temp_dir, "integration.json")
            security_path = os.path.join(temp_dir, "security.json")
            automation_path = os.path.join(temp_dir, "automation.json")
            
            config_manager.save_config(integration_config.to_dict(), integration_path)
            config_manager.save_config(security_config.to_dict(), security_path)
            config_manager.save_config(automation_config.to_dict(), automation_path)
            
            # Load and verify
            loaded_integration = config_manager.load_config(integration_path)
            loaded_security = config_manager.load_config(security_path)
            loaded_automation = config_manager.load_config(automation_path)
            
            self.assertEqual(loaded_integration["service_name"], "github")
            self.assertEqual(loaded_security["default_permission"], "L2")
            self.assertTrue(loaded_automation["enabled"])
            
            # Get as objects
            int_config = config_manager.get_config(integration_path, IntegrationConfig)
            sec_config = config_manager.get_config(security_path, SecurityConfig)
            auto_config = config_manager.get_config(automation_path, AutomationConfig)
            
            self.assertIsInstance(int_config, IntegrationConfig)
            self.assertIsInstance(sec_config, SecurityConfig)
            self.assertIsInstance(auto_config, AutomationConfig)
            
        finally:
            # Clean up
            for f in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, f))
            os.rmdir(temp_dir)

    def test_config_validation_workflow(self):
        """Test configuration validation workflow"""
        config_manager = ConfigManager()
        
        # Valid config
        valid_config = {
            "integration": {"github": {"enabled": True}},
            "security": {"default_permission": "L2"}
        }
        
        # Should not raise
        config_manager.validate_config(
            valid_config,
            required_keys=["integration", "security"],
            schema={
                "integration": dict,
                "security": dict
            }
        )
        
        # Invalid config - missing keys
        invalid_config = {"integration": {"github": {"enabled": True}}}
        
        with self.assertRaises(ConfigValidationError):
            config_manager.validate_config(
                invalid_config,
                required_keys=["integration", "security"]
            )


if __name__ == '__main__':
    unittest.main()
