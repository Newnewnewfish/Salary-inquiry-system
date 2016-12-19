from werkzeug.security import generate_password_hash, check_password_hash
from markdown import markdown
import bleach
from flask import current_app, request
from flask.ext.login import UserMixin, AnonymousUserMixin
from . import db, login_manager


class Permission:
    READ = 0x01 #读取工资数据权限
    INPUT = 0x02 #写入工资数据权限
    ADMINISTER = 0x04 #管理员权限


class Role(db.Model):
	'''用户角色类型的ORM模型
		包含id, name, defualt, permissions四个字段
		并提供id作为表users的外键引用
	'''
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
		'''初始化用户角色，定义普通用户read权限，
			HR用户录入权限，管理帐号权限
		'''
		roles = {
            'User': (Permission.READ, True),
            'HR': (Permission.READ |
                          Permission.INPUT, False),
            'Administrator': (0x0f, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
	'''用户帐号的ORM模型
		包含id, username, role_id, password_hash四个字段，
		其中role_id为外键引用自表roles的id字段
		并提供id作为表posts的外键引用
	'''
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    def __init__(self, **kwargs):
	'''定义默认用户角色'''
        super(User, self).__init__(**kwargs)
        if self.role is None:
			self.role = Role.query.filter_by(default=True).first()

    @property
    def password(self):
        '''禁止读取password'''
		raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
		'''设置密码并保存密码的散列值'''
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
		'''校检密码'''
        return check_password_hash(self.password_hash, password)

    def can(self, permissions):
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
	'''对匿名用户不提供权限'''
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    '''加载用户的回调函数'''
	return User.query.get(int(user_id))


class Post(db.Model):
	'''工资数据的ORM模型
		包含id, body, body_html, author_id四个字段
		其中author_id为外键，引用自表users的id字段
	'''
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
	'''处理工资数据文本'''
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p', 'tr' , 'table' , 'td' ] #仅允许文本中存在以上html标签
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True)) #将markdown文本转化为html文本

db.event.listen(Post.body, 'set', Post.on_changed_body) #监听文本录入
