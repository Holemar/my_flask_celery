fc_agent = db.getSiblingDB("my_flask_celery");

fc_agent.user.createIndex({"user_name": 1}, {"backgroud":true});
fc_agent.user.createIndex({"email": 1}, {"backgroud":true});
fc_agent.user.createIndex({"mobile": 1}, {"backgroud":true});

fc_agent.project.createIndex({"user_id": 1}, {"backgroud":true});
fc_agent.session.createIndex({"user_id": 1}, {"backgroud":true});

