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


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
