class SystemRouter:
    """
    Traffic Controller for Database Operations.
    
    1. System DB ('system'):
       - Users & Passwords (auth)
       - Sessions (Login status)
       - Admin Logs
       - Licensing Logic (ClientLicense, UsedLicense, LicenseHistory)
       
    2. Business DB ('default'):
       - Everything else (Receipts, Inventory, CompanySettings, etc.)
    """
    
    # Apps that ALWAYS go to System DB
    route_app_labels = {
        'auth',           # Users, Groups, Permissions
        'contenttypes',   # Django Core
        'sessions',       # Login Sessions
        'admin',          # Admin Panel Logs
    }
    
    # Specific Models from 'salesapp' that go to System DB
    system_models = {
        'clientlicense', 
        'usedlicense', 
        'licensehistory',
    }

    def db_for_read(self, model, **hints):
        """Read from 'system' if it's a system model, else 'default'."""
        if model._meta.app_label in self.route_app_labels or model._meta.model_name in self.system_models:
            return 'system'
        return 'default'

    def db_for_write(self, model, **hints):
        """Write to 'system' if it's a system model, else 'default'."""
        if model._meta.app_label in self.route_app_labels or model._meta.model_name in self.system_models:
            return 'system'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations between objects in different databases."""
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure tables are created in the correct database."""
        is_system_model = (
            app_label in self.route_app_labels or 
            model_name in self.system_models
        )
        
        if is_system_model:
            return db == 'system'  # System models -> System DB Only
        else:
            return db == 'default' # Business models -> Default DB Only
