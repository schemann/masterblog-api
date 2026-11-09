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


@app.route('/api/posts', methods=['GET'])
def get_posts():
    """Return all blog posts as JSON."""
    return jsonify(POSTS)


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

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
