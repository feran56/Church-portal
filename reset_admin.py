from app import app, db, User

with app.app_context():

    user = User.query.filter_by(username="admin").first()

    if user:
        user.password = "love"
        db.session.commit()
        print("✅ Admin password reset to: love")
    else:
        print("❌ Admin not found")
