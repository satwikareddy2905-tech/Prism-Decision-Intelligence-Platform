"""
Seed script for Prism — populates database with realistic SaaS decision data.
Creates database tables automatically if they do not exist.
"""

from datetime import datetime, timedelta
from app import create_app
from app.extensions import db, bcrypt
from app.models import (
    User, Decision, Criterion, Option, CustomAttribute, Score, JournalEntry, ActivityLog
)

app = create_app()

def seed():
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()


        # Check if demo user already exists
        demo_user = User.query.filter_by(username='alexm').first()
        if demo_user:
            print("Database already seeded.")
            return

        print("Seeding Prism database with initial SaaS demo data...")

        # 1. Create Demo User
        hashed_pwd = bcrypt.generate_password_hash('password123').decode('utf-8')
        user = User(
            username='alexm',
            email='alex.morgan@example.com',
            full_name='Alex Morgan',
            password_hash=hashed_pwd,
            email_verified=True,
            dark_mode=False
        )
        db.session.add(user)
        db.session.flush()

        # 2. Decision 1: Buy Work Laptop (Active / Completed)
        d1 = Decision(
            user_id=user.id,
            title='Selecting High-Performance Work Laptop',
            category='Technology',
            goal='Choose a reliable, portable laptop for software design and 4K video editing under $2,500.',
            description='Comparing top flagship workstation laptops based on battery, build, performance, and thermal management.',
            status='completed',
            privacy='private',
            deadline=datetime.utcnow().date() + timedelta(days=5),
            pinned=True,
            confidence_score=92.0
        )
        db.session.add(d1)
        db.session.flush()

        # Criteria for D1
        c1 = Criterion(decision_id=d1.id, name='Processing Performance', weight=9.0, priority='critical', is_mandatory=True, sort_order=1)
        c2 = Criterion(decision_id=d1.id, name='Battery Life', weight=8.0, priority='high', is_mandatory=False, sort_order=2)
        c3 = Criterion(decision_id=d1.id, name='Display Quality & Color Accuracy', weight=7.5, priority='high', is_mandatory=False, sort_order=3)
        c4 = Criterion(decision_id=d1.id, name='Price / Value', weight=6.5, priority='medium', is_mandatory=False, sort_order=4)
        c5 = Criterion(decision_id=d1.id, name='Portability & Weight', weight=5.0, priority='medium', is_mandatory=False, sort_order=5)
        db.session.add_all([c1, c2, c3, c4, c5])
        db.session.flush()

        # Options for D1
        o1 = Option(decision_id=d1.id, name='MacBook Pro 16" M3 Max', price=2499.00, notes='Outstanding battery and thermal efficiency. M3 chip delivers exceptional single-core and GPU performance.', sort_order=1)
        o2 = Option(decision_id=d1.id, name='Dell XPS 16 (i9 / RTX 4070)', price=2299.00, notes='Sleek design, 4K OLED touch display, but battery life drops during heavy load.', sort_order=2)
        o3 = Option(decision_id=d1.id, name='Lenovo ThinkPad P1 Gen 6', price=2150.00, notes='Legendary keyboard and durability, extensive port selection.', sort_order=3)
        db.session.add_all([o1, o2, o3])
        db.session.flush()

        d1.final_choice_id = o1.id

        # Custom Attributes for D1 options
        db.session.add_all([
            CustomAttribute(option_id=o1.id, attr_key='RAM', attr_value='36 GB Unified'),
            CustomAttribute(option_id=o1.id, attr_key='Storage', attr_value='1 TB SSD'),
            CustomAttribute(option_id=o2.id, attr_key='RAM', attr_value='32 GB DDR5'),
            CustomAttribute(option_id=o2.id, attr_key='Storage', attr_value='1 TB SSD')
        ])

        # Scores for D1
        scores_d1 = [
            # MacBook
            Score(decision_id=d1.id, criterion_id=c1.id, option_id=o1.id, raw_score=9.5),
            Score(decision_id=d1.id, criterion_id=c2.id, option_id=o1.id, raw_score=9.5),
            Score(decision_id=d1.id, criterion_id=c3.id, option_id=o1.id, raw_score=9.0),
            Score(decision_id=d1.id, criterion_id=c4.id, option_id=o1.id, raw_score=6.5),
            Score(decision_id=d1.id, criterion_id=c5.id, option_id=o1.id, raw_score=7.5),
            # Dell XPS
            Score(decision_id=d1.id, criterion_id=c1.id, option_id=o2.id, raw_score=8.5),
            Score(decision_id=d1.id, criterion_id=c2.id, option_id=o2.id, raw_score=6.0),
            Score(decision_id=d1.id, criterion_id=c3.id, option_id=o2.id, raw_score=9.5),
            Score(decision_id=d1.id, criterion_id=c4.id, option_id=o2.id, raw_score=7.0),
            Score(decision_id=d1.id, criterion_id=c5.id, option_id=o2.id, raw_score=7.0),
            # Lenovo ThinkPad
            Score(decision_id=d1.id, criterion_id=c1.id, option_id=o3.id, raw_score=8.0),
            Score(decision_id=d1.id, criterion_id=c2.id, option_id=o3.id, raw_score=7.0),
            Score(decision_id=d1.id, criterion_id=c3.id, option_id=o3.id, raw_score=8.0),
            Score(decision_id=d1.id, criterion_id=c4.id, option_id=o3.id, raw_score=8.0),
            Score(decision_id=d1.id, criterion_id=c5.id, option_id=o3.id, raw_score=6.5),
        ]
        db.session.add_all(scores_d1)

        # Journal entry for D1
        j1 = JournalEntry(
            decision_id=d1.id,
            user_id=user.id,
            outcome='Purchased the MacBook Pro 16". The battery life easily lasts a full day of heavy development without plugging in.',
            reflection='Extremely satisfied with the thermal performance and quiet operation.',
            lessons_learned='Prioritizing battery efficiency over raw peak GPU power paid off for remote working.',
            satisfaction_score=9,
            would_choose_again=True
        )
        db.session.add(j1)

        # 3. Decision 2: Senior Career Offer (Active)
        d2 = Decision(
            user_id=user.id,
            title='Evaluating Career Move: Startup vs Enterprise',
            category='Career',
            goal='Decide between staying at Enterprise Corp vs joining Series-B AI Startup as Lead Engineer.',
            description='Weighing equity upside, work-life balance, remote flexibility, and compensation package.',
            status='active',
            privacy='private',
            deadline=datetime.utcnow().date() + timedelta(days=12),
            pinned=True
        )
        db.session.add(d2)
        db.session.flush()

        c2_1 = Criterion(decision_id=d2.id, name='Total Compensation & Equity', weight=9.5, priority='critical', sort_order=1)
        c2_2 = Criterion(decision_id=d2.id, name='Career Growth & Learning', weight=9.0, priority='high', sort_order=2)
        c2_3 = Criterion(decision_id=d2.id, name='Work-Life Balance & Remote Flexibility', weight=8.0, priority='high', sort_order=3)
        c2_4 = Criterion(decision_id=d2.id, name='Company Stability', weight=6.0, priority='medium', sort_order=4)
        db.session.add_all([c2_1, c2_2, c2_3, c2_4])
        db.session.flush()

        o2_1 = Option(decision_id=d2.id, name='Series-B AI Startup (Lead Engineer)', notes='$180k Base + 0.5% Equity. Fast-paced, high responsibility.', sort_order=1)
        o2_2 = Option(decision_id=d2.id, name='Current Enterprise (Senior Software Engineer)', notes='$165k Base + $25k Bonus. High job stability, predictable hours.', sort_order=2)
        db.session.add_all([o2_1, o2_2])
        db.session.flush()

        scores_d2 = [
            Score(decision_id=d2.id, criterion_id=c2_1.id, option_id=o2_1.id, raw_score=9.0),
            Score(decision_id=d2.id, criterion_id=c2_2.id, option_id=o2_1.id, raw_score=9.5),
            Score(decision_id=d2.id, criterion_id=c2_3.id, option_id=o2_1.id, raw_score=7.0),
            Score(decision_id=d2.id, criterion_id=c2_4.id, option_id=o2_1.id, raw_score=6.0),

            Score(decision_id=d2.id, criterion_id=c2_1.id, option_id=o2_2.id, raw_score=7.5),
            Score(decision_id=d2.id, criterion_id=c2_2.id, option_id=o2_2.id, raw_score=6.5),
            Score(decision_id=d2.id, criterion_id=c2_3.id, option_id=o2_2.id, raw_score=8.5),
            Score(decision_id=d2.id, criterion_id=c2_4.id, option_id=o2_2.id, raw_score=9.0),
        ]
        db.session.add_all(scores_d2)

        # 4. Activity Logs
        logs = [
            ActivityLog(user_id=user.id, decision_id=d1.id, action='created_decision', description='Created decision "Selecting High-Performance Work Laptop"'),
            ActivityLog(user_id=user.id, decision_id=d1.id, action='scored_option', description='Evaluated options against criteria'),
            ActivityLog(user_id=user.id, decision_id=d1.id, action='completed_decision', description='Marked as completed with MacBook Pro 16"'),
            ActivityLog(user_id=user.id, decision_id=d1.id, action='added_journal', description='Added post-decision reflection'),
            ActivityLog(user_id=user.id, decision_id=d2.id, action='created_decision', description='Created decision "Evaluating Career Move: Startup vs Enterprise"')
        ]
        db.session.add_all(logs)

        db.session.commit()
        print("Seeding complete! User 'alexm' created with password 'password123'.")

if __name__ == '__main__':
    seed()
