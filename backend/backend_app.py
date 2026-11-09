"""Masterblog API: a JSON API for blog posts, built with Flask."""
from datetime import date, datetime

from flask import Blueprint, Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

# Rate limiting per client IP for every route; 429 answers carry a Retry-After header
limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["100 per minute"],
                  storage_uri="memory://", headers_enabled=True)

# All endpoints live in one blueprint, registered twice: under /api (used by the frontend)
# and under /api/v1 (the versioned path; a future v2 can change the contract without
# breaking v1 clients).
api = Blueprint('api', __name__)

POSTS = [
    {"id": 1, "title": "First post", "content": "This is the first post.",
     "author": "John Doe", "date": "2023-06-07"},
    {"id": 2, "title": "Second post", "content": "This is the second post.",
     "author": "Jane Doe", "date": "2023-06-08"},
]

DATE_FORMAT = "%Y-%m-%d"
DEFAULT_AUTHOR = "Anonymous"
REQUIRED_FIELDS = ("title", "content")
TEXT_FIELDS = ("title", "content", "author")
POST_FIELDS = ("title", "content", "author", "date")
SORT_FIELDS = POST_FIELDS
SEARCH_FIELDS = POST_FIELDS
SORT_DIRECTIONS = ("asc", "desc")


def parse_date(value):
    """Return the date for a 'YYYY-MM-DD' string; raise ValueError otherwise."""
    if not isinstance(value, str):
        raise ValueError("date must be a string in the format YYYY-MM-DD.")
    try:
        return datetime.strptime(value.strip(), DATE_FORMAT).date()
    except ValueError as error:
        raise ValueError("date must be a valid date in the format YYYY-MM-DD.") from error


def missing_fields(data):
    """Return the required fields that are missing or empty in the request data."""
    if not isinstance(data, dict):
        return list(REQUIRED_FIELDS)
    return [field for field in REQUIRED_FIELDS
            if not isinstance(data.get(field), str) or not data[field].strip()]


def clean_fields(data):
    """Return the post fields present in data, stripped and checked; raise ValueError.

    title, content and author must be non-empty strings, date must be 'YYYY-MM-DD'.
    """
    cleaned = {}
    for field in TEXT_FIELDS:
        if field in data:
            value = data[field]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must not be empty.")
            cleaned[field] = value.strip()
    if "date" in data:
        cleaned["date"] = parse_date(data["date"]).strftime(DATE_FORMAT)
    return cleaned


def next_post_id():
    """Return a new unique integer id: one higher than the highest id in use."""
    return max((post["id"] for post in POSTS), default=0) + 1


def find_post_by_id(post_id):
    """Return the post with this id, or None if there is none."""
    for post in POSTS:
        if post["id"] == post_id:
            return post
    return None


def sort_key(field):
    """Return a sort key for a post field: real dates for 'date', lower-case text otherwise."""
    if field == "date":
        return lambda post: parse_date(post["date"])
    return lambda post: post[field].lower()


def sort_posts(posts):
    """Sort posts by ?sort=<field>&direction=asc|desc; raise ValueError if invalid.

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
    return sorted(posts, key=sort_key(sort_field), reverse=direction == 'desc')


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


@api.route('/posts', methods=['GET'])
def get_posts():
    """Return all blog posts as JSON, optionally sorted and paginated.

    Query parameters: sort=title|content|author|date, direction=asc|desc, page, limit.
    """
    try:
        return posts_response(sort_posts(POSTS))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@api.route('/posts', methods=['POST'])
def add_post():
    """Add a new post from the JSON body; return it with 201.

    title and content are required; author defaults to "Anonymous", date to today.
    """
    data = request.get_json(silent=True)
    missing = missing_fields(data)
    if missing:
        return jsonify({"error": "Missing required fields", "missing": missing}), 400
    try:
        fields = clean_fields(data)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    new_post = {
        "id": next_post_id(),
        "title": fields["title"],
        "content": fields["content"],
        "author": fields.get("author", DEFAULT_AUTHOR),
        "date": fields.get("date", date.today().strftime(DATE_FORMAT)),
    }
    POSTS.append(new_post)
    return jsonify(new_post), 201


@api.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    """Delete the post with this id; 404 if it does not exist."""
    post = find_post_by_id(post_id)
    if post is None:
        return jsonify({"error": f"Post with id {post_id} was not found."}), 404
    POSTS.remove(post)
    return jsonify({"message": f"Post with id {post_id} has been deleted successfully."}), 200


@api.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    """Update title, content, author and/or date; fields left out keep their value."""
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
    try:
        fields = clean_fields(data)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    post.update(fields)
    return jsonify(post), 200


@api.route('/posts/search', methods=['GET'])
def search_posts():
    """Return posts where any given field contains its search term.

    Query parameters: title, content, author, date (e.g. date=2023-06). The search ignores
    upper and lower case; several terms match posts that fit any of them. Without search
    terms all posts are returned. The result can be paginated with page and limit.
    """
    terms = {field: request.args.get(field, "").strip().lower() for field in SEARCH_FIELDS}
    terms = {field: term for field, term in terms.items() if term}
    results = POSTS
    if terms:
        results = [post for post in POSTS
                   if any(term in post[field].lower() for field, term in terms.items())]
    try:
        return posts_response(results)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(api, url_prefix='/api/v1', name='api_v1')


@app.errorhandler(429)
def rate_limit_error(error):
    """Answer a client over its rate limit with a JSON error."""
    response = jsonify({"error": f"Too Many Requests: {error.description}"})
    response.status_code = 429
    return response


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
