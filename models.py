from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# 4-4. 유사약재그룹
class SimilarityGroup(db.Model):
    # PK, FK
    group_id = db.Column(db.Integer, primary_key=True)
    # 일반속성
    group_name = db.Column(db.String(255))
    # 각 테이블에 대한 관계설정
    herb = db.relationship('Herb', backref="group_id")

    def __repr__(self):
        return '<SimilarityGroup %r>' % (self.group_name)


# 4-5. 한방분류그룹
class Category(db.Model):
    # PK, FK
    category_id = db.Column(db.Integer, primary_key=True)
    # 일반속성
    category_name = db.Column(db.String(255))
    # 각 테이블에 대한 관계설정
    herb = db.relationship('Herb', backref="category_id")

    def __repr__(self):
        return '<Category %r>' % (self.category_name)


class Herb(db.Model):
    __table_args__ = (
        db.CheckConstraint('is_poison = 0 or is_poison = 1'),
    )
    # PK, FK
    herb_id = db.Column(db.Integer, primary_key=True)  # PK면서, Location의 FK -> Location에서 선택당해야함
    group_id_fk = db.Column(db.Integer, db.ForeignKey('similarity_group.group_id'))
    category_id_fk = db.Column(db.Integer, db.ForeignKey('category.category_id'))

    # 일반속성
    herb_name = db.Column(db.String(100))
    major_effect = db.Column(db.String(50))
    effect = db.Column(db.String(255))
    origin = db.Column(db.String(255))
    scientific_name = db.Column(db.String(255))
    is_poison = db.Column(db.Integer, db.CheckConstraint('is_poison = 0 or is_poison = 1'))  # 확인필요
    figure_feature = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.Text, nullable=True)
    # 각 테이블에 대한 관계설정 (admin에서 나와버리니까 안나오도록)
    location = db.relationship('Location', backref="herb_id")
    news = db.relationship('News', backref="herb_id")
    journal = db.relationship('Journal', backref="herb_id")

    def __repr__(self):
        return '<Herb %r>' % (self.herb_name)


# 4-3. Location
class Location(db.Model):
    # PK, FK
    location_id = db.Column(db.Integer, primary_key=True)
    herb_id_fk = db.Column(db.Integer, db.ForeignKey('herb.herb_id'))  # FK인데, 자기쪽에선 PK

    # 일반속성
    country = db.Column(db.String(150))
    location_name = db.Column(db.String(150), nullable=True)  # 지역명! 지역명없을땐 국가는 외국
    pos_x = db.Column(db.Float)
    pos_y = db.Column(db.Float)

    def __repr__(self):
        return '<Location %r>' % (self.location_name)


# 4-7. 뉴스
class News(db.Model):
    # PK, FK
    news_id = db.Column(db.Integer, primary_key=True)
    herb_id_fk = db.Column(db.Integer, db.ForeignKey('herb.herb_id'))
    # 일반속성
    title = db.Column(db.Text)
    date = db.Column(db.DateTime)
    content = db.Column(db.Text)
    url = db.Column(db.String(255))

    def __repr__(self):
        return '<News %r>' % (self.news_id)


# 4-6. 논문
class Journal(db.Model):
    # PK, FK
    journal_id = db.Column(db.Integer, primary_key=True)
    herb_id_fk = db.Column(db.Integer, db.ForeignKey('herb.herb_id'))
    # 일반속성
    title = db.Column(db.Text)
    date = db.Column(db.DateTime)
    url = db.Column(db.String(255))

    def __repr__(self):
        return '<Journal %r>' % (self.journal_id)
