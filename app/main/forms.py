from flask.ext.wtf import Form
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField, PasswordField
from wtforms.validators import Required, Length, Email, Regexp, NumberRange,\
	EqualTo
from wtforms import ValidationError
from flask.ext.pagedown.fields import PageDownField
from ..models import Role, User

	
class AdminForm(Form):
	'''管理表单，供管理员帐号修改其他注册用户帐号信息'''
	username = StringField('Username', validators=[
		Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
										'Usernames must have only letters, '
										'numbers, dots or underscores')])
	role = SelectField('Role', coerce=int)
	password = PasswordField('Password', validators=[
		Required(), EqualTo('password2', message='Passwords must match.')])
	password2 = PasswordField('Confirm password', validators=[Required()])
	submit = SubmitField('Submit')

	def __init__(self, user, *args, **kwargs):
		super(AdminForm, self).__init__(*args, **kwargs)
		self.role.choices = [(role.id, role.name)
							for role in Role.query.order_by(Role.name).all()]
		self.user = user

	def validate_username(self, field):
		if field.data != self.user.username and \
				User.query.filter_by(username=field.data).first():
			raise ValidationError('Username already in use.')


class PostForm(Form):
	'''数据录入表单'''
	id = StringField('Please input the employee number:',validators=[Required()])
	body = PageDownField("Please input the salary data:", validators=[Required()])
	submit = SubmitField('Submit')
