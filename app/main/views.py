from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app
from flask.ext.login import login_required, current_user
from . import main
from .forms import AdminForm, PostForm
from .. import db
from ..models import Permission, Role, User, Post
from ..decorators import admin_required, hr_required


@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.INPUT) and \
           form.validate_on_submit():
        post = Post(body=form.body.data,
                    author_id=form.id.data)
        db.session.add(post)
        return redirect(url_for('.index'))
    if current_user.can(Permission.READ):
		page = request.args.get('page', 1, type=int)
		pagination = Post.query.paginate(
			page, per_page=current_app.config['POSTS_PER_PAGE'],
			error_out=False)
		posts = pagination.items
		return render_template('index.html', form=form, posts=posts,
							pagination=pagination)
    return render_template('index.html',form=form)

@main.route('/user/<int:id>')
@login_required
@hr_required
def user(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts,
                           pagination=pagination)


	
@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = AdminForm(user=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.role = Role.query.get(form.role.data)
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.username.data = user.username
    form.role.data = user.role_id
    return render_template('edit_profile.html', form=form, user=user)
