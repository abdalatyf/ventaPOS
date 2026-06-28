class SystemDBRouter:
    """
    A router to control all database operations on models in the
    auth, contenttypes, sessions, admin applications, and specific api models.
    """
    
    system_apps = {'auth', 'contenttypes', 'sessions', 'admin'}
    system_models = {'clientlicense', 'usedlicense', 'licensehistory', 'actionlog'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.system_apps:
            return 'system'
        if model._meta.app_label == 'api' and model._meta.model_name in self.system_models:
            return 'system'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.system_apps:
            return 'system'
        if model._meta.app_label == 'api' and model._meta.model_name in self.system_models:
            return 'system'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations if both objects are in the system db, or both in default db
        obj1_db = 'system' if (obj1._meta.app_label in self.system_apps or (obj1._meta.app_label == 'api' and obj1._meta.model_name in self.system_models)) else 'default'
        obj2_db = 'system' if (obj2._meta.app_label in self.system_apps or (obj2._meta.app_label == 'api' and obj2._meta.model_name in self.system_models)) else 'default'
        
        if obj1_db == obj2_db:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.system_apps:
            return db == 'system'
        if app_label == 'api' and model_name in self.system_models:
            return db == 'system'
        
        # If it's a known system app or model, it goes to system. Otherwise, default.
        return db == 'default'
