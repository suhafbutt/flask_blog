import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db, bcrypt
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from flaskblog.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required


# posts = [
# 	{
# 		'author': 'Jennifer Lopez',
# 		'title': 'Blog Post 1',
# 		'content': 'First post content',
# 		'date_posted': 'March 11, 2019'
# 	},
# 	{
# 		'author': 'Jimmy Falon',
# 		'title': 'Blog Post 2',
# 		'content': 'Second post content',
# 		'date_posted': 'April 21, 2019'
# 	}
# ]

@app.route('/')
@app.route('/home')
@app.route('/index')
def index():
	posts = Post.query.all()
	return render_template('index.html', posts= posts)


@app.route('/about')
def about():
	return render_template('about.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('index'))

	form = RegistrationForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user = User(username=form.username.data, email=form.email.data, password=hashed_password)
		db.session.add(user)
		db.session.commit()
		flash(f"Your account has been created! now you are able to log in", 'success')
		return redirect(url_for('login'))

	return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('index'))

	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password, form.password.data):
			login_user(user, remember=form.remember.data)
			# flash('You have been logged in!', 'success')
			next_page = request.args.get('next')
			# return redirect(url_for(next_page)) if next_page else redirect(url_for('/index'))
			return redirect(url_for(next_page.strip("/") if next_page else 'index' ))
		else:
			flash('Login unseccessful. Please check email and password.', 'danger')


	return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('index'))


def save_picture(form_picture):
	random_hex = secrets.token_hex(8)
	_, p_ext = os.path.splitext(form_picture.filename)
	randomized_filename = random_hex + p_ext
	picture_path = os.path.join(app.root_path, 'static/profile_pics', randomized_filename)
	output_size = (125, 125)
	i = Image.open(form_picture)
	i.thumbnail(output_size)
	i.save(picture_path)
	return randomized_filename

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
	form = UpdateAccountForm()
	if form.validate_on_submit():
		if form.image_file.data:
			saved_picture_name = save_picture(form.image_file.data)
			current_user.image_file = saved_picture_name

		current_user.username = form.username.data
		current_user.email = form.email.data
		db.session.commit()
		flash(f"Your account has been updated!", 'success')
		return redirect(url_for('account'))
	elif request.method == 'GET':
		form.username.data = current_user.username
		form.email.data = current_user.email

	profile_pic = url_for('static', filename='profile_pics/' + current_user.image_file)
	return render_template('account.html', title='Account', profile_pic=profile_pic, form=form)

@app.route('/posts/new', methods=['GET', 'POST'])
@login_required
def new_post():
	form = PostForm()
	if form.validate_on_submit():
		post = Post(title=form.title.data, content=form.content.data, author=current_user)
		db.session.add(post)
		db.session.commit()
		flash(f"Your post has been created!", 'success')
		return redirect(url_for('index'))

	return render_template('create_post.html', title='New Post', form=form, legend='New Post')

@app.route('/posts/<int:post_id>', methods=['GET'])
@login_required
def post(post_id):
	post = Post.query.get_or_404(post_id)
	return render_template('post.html', title='Post', post=post)

@app.route('/posts/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
	post = Post.query.get_or_404(post_id)
	if post.author != current_user:
		abort(403)
	form = PostForm()
	if form.validate_on_submit():
		post.title = form.title.data
		post.content = form.content.data
		db.session.commit()
		flash(f"Your post has been update!", 'success')
		return redirect(url_for('post', post_id=post.id))
	elif request.method == 'GET':
		form.title.data = post.title
		form.content.data = post.content
	return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')

@app.route('/posts/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
	post = Post.query.get_or_404(post_id)
	if post.author != current_user:
		abort(403)

	db.session.delete(post)
	db.session.commit()
	flash(f"Your post has been deleted!", 'success')
	return redirect(url_for('index'))
