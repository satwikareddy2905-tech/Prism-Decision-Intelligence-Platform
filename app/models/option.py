from datetime import datetime
from app.extensions import db


class Option(db.Model):
    __tablename__ = 'options'

    id = db.Column(db.Integer, primary_key=True)
    decision_id = db.Column(db.Integer, db.ForeignKey('decisions.id', ondelete='CASCADE'),
                             nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(12, 2), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    url = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    scores = db.relationship('Score', backref='option', lazy='dynamic',
                              cascade='all, delete-orphan',
                              foreign_keys='Score.option_id')
    custom_attributes = db.relationship('CustomAttribute', backref='option', lazy='dynamic',
                                         cascade='all, delete-orphan')

    @property
    def formatted_price(self):
        if self.price is None:
            return None
        return f'${self.price:,.2f}'

    @property
    def attributes_list(self):
        return [{'key': attr.attr_key, 'value': attr.attr_value} for attr in self.custom_attributes]

    def __repr__(self):
        return f'<Option {self.name}>'


class CustomAttribute(db.Model):
    __tablename__ = 'custom_attributes'

    id = db.Column(db.Integer, primary_key=True)
    option_id = db.Column(db.Integer, db.ForeignKey('options.id', ondelete='CASCADE'),
                           nullable=False, index=True)
    attr_key = db.Column(db.String(100), nullable=False)
    attr_value = db.Column(db.String(300), nullable=True)

    def __repr__(self):
        return f'<Attribute {self.attr_key}: {self.attr_value}>'
