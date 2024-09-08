fc_agent = db.getSiblingDB("my_flask_celery");

fc_agent.user.createIndex({"user_name": 1}, {"name": "user_name"});
fc_agent.user.createIndex({"email": 1}, {"name": "email"});
fc_agent.user.createIndex({"mobile": 1}, {"name": "mobile"});

fc_agent.project.createIndex({"user_id": 1}, {"name": "user_id"});
fc_agent.session.createIndex({"user_id": 1}, {"name": "user_id"});
