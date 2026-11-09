"""Masterblog API: a JSON API for blog posts, built with Flask."""
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

POSTS = [
    {"id": 1, "title": "First post", "content": "This is the first post."},
    {"id": 2, "title": "Second post", "content": "This is the second post."},
]

REQUIRED_FIELDS = ("title", "content")
SORT_FIELDS = ("title", "content")
SORT_DIRECTIONS = ("asc", "desc")


def missing_fields(data):
    """Return the required fields that are missing or empty in the request data."""
    if not isinstance(data, dict):
        return list(REQUIRED_FIELDS)
    return [field for field in REQUIRED_FIELDS
            if not isinstance(data.get(field), str) or not data[field].strip()]


def next_post_id():
    """Return a new unique integer id: one higher than the highest id in use."""
    return max((post["id"] for post in POSTS), default=0) + 1


def find_post_by_id(post_id):
    """Return the post with this id, or None if there is none."""
    for post in POSTS:
        if post["id"] == post_id:
            return post
    return None


def sort_posts(posts):
    """Sort posts by ?sort=title|content&direction=asc|desc; raise ValueError if invalid.

    Without these parameters the posts keep their original order.
    """
    sort_field = request.args.get('sort')
    direction = request.args.get('direction')
    if sort_field is None and direction is None:
        return posts
    if sort_field is None:
        raise ValueError("direction needs a sort field, e.g. ?sort=title")
    if sort_field not in SORT_FIELDS:
        raise ValueError(f"Invalid sort field '{sort_field}'. "
                         f"Use one of: {', '.join(SORT_FIELDS)}.")
    direction = direction or 'asc'
    if direction not in SORT_DIRECTIONS:
        raise ValueError(f"Invalid direction '{direction}'. "
                         f"Use one of: {', '.join(SORT_DIRECTIONS)}.")
    return sorted(posts, key=lambda post: post[sort_field].lower(),
                  reverse=direction == 'desc')


def read_positive_int(name, default):
    """Return the query parameter `name` as an int >= 1; raise ValueError otherwise."""
    value = request.args.get(name, str(default))
    if not value.isdigit() or int(value) < 1:
        raise ValueError(f"{name} must be a whole number of 1 or higher.")
    return int(value)


def paginate_posts(posts):
    """Return one page of posts for ?page=&limit= (limit defaults to 10, page to 1).

    Without both parameters all posts are returned.
    """
    if 'page' not in request.args and 'limit' not in request.args:
        return posts
    page = read_positive_int('page', 1)
    limit = read_positive_int('limit', 10)
    start_index = (page - 1) * limit
    return posts[start_index:start_index + limit]


def posts_response(posts):
    """Return the posts as JSON, with the total count before pagination in X-Total-Count."""
    response = jsonify(paginate_posts(posts))
    response.headers['X-Total-Count'] = str(len(posts))
    return response


@app.route('/api/posts', methods=['GET'])
def get_posts():
    """Return all blog posts as JSON, optionally sorted and paginated.

    Query parameters: sort=title|content, direction=asc|desc, page, limit.
    """
    try:
        return posts_response(sort_posts(POSTS))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@app.route('/api/posts', methods=['POST'])
def add_post():
    """Add a new post from the JSON body {"title", "content"}; return it with 201."""
    data = request.get_json(silent=True)
    missing = missing_fields(data)
    if missing:
        return jsonify({"error": "Missing required fields", "missing": missing}), 400

    new_post = {
        "id": next_post_id(),
        "title": data["title"].strip(),
        "content": data["content"].strip(),
    }
    POSTS.append(new_post)
    return jsonify(new_post), 201



@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    """Delete the post with this id; 404 if it does not exist."""
    post = find_post_by_id(post_id)
    if post is None:
        return jsonify({"error": f"Post with id {post_id} was not found."}), 404
    POSTS.remove(post)
    return jsonify({"message": f"Post with id {post_id} has been deleted successfully."}), 200


@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    """Update title and/or content of a post; fields left out keep their value."""
    post = find_post_by_id(post_id)
    if post is None:
        return jsonify({"error": f"Post with id {post_id} was not found."}), 404

    # An empty body means "no changes"; a body that is not a JSON object is an error
    data = request.get_json(silent=True)
    if data is None and request.get_data():
        data = []
    data = {} if data is None else data
    if not isinstance(data, dict):
        return jsonify({"error": "The request body must be a JSON object."}), 400

    invalid = [field for field in REQUIRED_FIELDS
               if field in data and (not isinstance(data[field], str) or not data[field].strip())]
    if invalid:
        return jsonify({"error": "Fields must not be empty", "invalid": invalid}), 400

    for field in REQUIRED_FIELDS:
        if field in data:
            post[field] = data[field].strip()
    return jsonify(post), 200


@app.route('/api/posts/search', methods=['GET'])
def search_posts():
    """Return posts whose title contains ?title=... or whose content contains ?content=...

    The search ignores upper and lower case. Without search terms all posts are returned.
    The result can be paginated with page and limit like the list endpoint.
    """
    terms = {field: request.args.get(field, "").strip().lower() for field in REQUIRED_FIELDS}
    terms = {field: term for field, term in terms.items() if term}
    results = POSTS
    if terms:
        results = [post for post in POSTS
                   if any(term in post[field].lower() for field, term in terms.items())]
    try:
        return posts_response(results)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
