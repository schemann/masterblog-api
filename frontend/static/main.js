// Function that runs once the window is fully loaded
window.onload = function() {
    // Attempt to retrieve the API base URL from the local storage
    var savedBaseUrl = localStorage.getItem('apiBaseUrl');
    // If a base URL is found in local storage, load the posts
    if (savedBaseUrl) {
        document.getElementById('api-base-url').value = savedBaseUrl;
        loadPosts();
    }
}

// Return the API base URL from the input field and remember it in local storage
function getBaseUrl() {
    var baseUrl = document.getElementById('api-base-url').value.trim().replace(/\/+$/, '');
    localStorage.setItem('apiBaseUrl', baseUrl);
    return baseUrl;
}

// Show a message above the posts; isError colours it red
function showStatus(message, isError) {
    var status = document.getElementById('status');
    status.textContent = message || '';
    status.className = isError ? 'status status-error' : 'status';
}

// Send a request and return the parsed JSON; reject with the API's error message on failure
function requestJson(url, options) {
    return fetch(url, options).then(response => {
        return response.json().catch(() => null).then(data => {
            if (!response.ok) {
                var message = data && data.error ? data.error : 'Request failed';
                if (data && data.missing) {
                    message += ': ' + data.missing.join(', ');
                }
                throw new Error(message + ' (HTTP ' + response.status + ')');
            }
            return data;
        });
    });
}

// Create an element with a class name and text; text is set safely, never as HTML
function createElement(tag, className, text) {
    var element = document.createElement(tag);
    if (className) {
        element.className = className;
    }
    if (text !== undefined) {
        element.textContent = text;
    }
    return element;
}

// Create a button that calls onClick when it is pressed
function createButton(label, className, onClick) {
    var button = createElement('button', className, label);
    button.onclick = onClick;
    return button;
}

// Show a list of posts on the page
function renderPosts(posts) {
    const postContainer = document.getElementById('post-container');
    postContainer.innerHTML = '';
    if (posts.length === 0) {
        postContainer.appendChild(createElement('p', 'empty', 'No posts found.'));
        return;
    }
    posts.forEach(post => postContainer.appendChild(createPostElement(post)));
}

// Build the element for one post: title, author and date, content and buttons
function createPostElement(post) {
    const postDiv = createElement('div', 'post');
    postDiv.appendChild(createElement('h2', null, post.title));
    postDiv.appendChild(createElement('p', 'meta',
        'by ' + (post.author || 'Anonymous') + ' on ' + (post.date || 'unknown date')));
    postDiv.appendChild(createElement('p', null, post.content));

    const actions = createElement('div', 'actions');
    actions.appendChild(createButton('Edit', 'button-edit', () => showEditForm(postDiv, post)));
    actions.appendChild(createButton('Delete', 'button-delete', () => deletePost(post.id)));
    postDiv.appendChild(actions);
    return postDiv;
}

// Replace a post on the page with a form to edit its fields
function showEditForm(postDiv, post) {
    postDiv.innerHTML = '';
    const fields = {};
    [['title', 'text'], ['content', 'text'], ['author', 'text'], ['date', 'date']].forEach(([name, type]) => {
        const input = createElement('input');
        input.type = type;
        input.value = post[name] || '';
        input.setAttribute('aria-label', name);
        input.placeholder = name;
        fields[name] = input;
        postDiv.appendChild(input);
    });
    const actions = createElement('div', 'actions');
    actions.appendChild(createButton('Save', 'button-edit', () => updatePost(post.id, fields)));
    actions.appendChild(createButton('Cancel', 'button-secondary', () => loadPosts()));
    postDiv.appendChild(actions);
}

// Function to fetch all the posts from the API and display them on the page.
// Returns a promise, so callers can show their own message after the reload.
function loadPosts() {
    var baseUrl = getBaseUrl();
    var sortField = document.getElementById('sort-field').value;
    var url = baseUrl + '/posts';
    if (sortField) {
        var direction = document.getElementById('sort-direction').value;
        url += '?sort=' + encodeURIComponent(sortField) + '&direction=' + encodeURIComponent(direction);
    }
    return requestJson(url)
        .then(posts => {
            renderPosts(posts);
            showStatus(sortField ? 'Sorted by ' + sortField + '.' : '');
        })
        .catch(error => showStatus(error.message, true));
}

// Function to search posts by the chosen field and show the results
function searchPosts() {
    var baseUrl = getBaseUrl();
    var field = document.getElementById('search-field').value;
    var term = document.getElementById('search-term').value.trim();
    if (!term) {
        loadPosts();
        return;
    }
    requestJson(baseUrl + '/posts/search?' + encodeURIComponent(field) + '=' + encodeURIComponent(term))
        .then(posts => {
            renderPosts(posts);
            showStatus(posts.length + ' post(s) with ' + field + ' containing "' + term + '".');
        })
        .catch(error => showStatus(error.message, true));
}

// Clear search and sorting and show all posts again
function resetView() {
    document.getElementById('search-term').value = '';
    document.getElementById('sort-field').value = '';
    loadPosts();
}

// Function to send a POST request to the API to add a new post
function addPost() {
    var baseUrl = getBaseUrl();
    var newPost = {
        title: document.getElementById('post-title').value,
        content: document.getElementById('post-content').value
    };
    var author = document.getElementById('post-author').value.trim();
    var date = document.getElementById('post-date').value;
    if (author) {
        newPost.author = author;
    }
    if (date) {
        newPost.date = date;
    }

    requestJson(baseUrl + '/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newPost)
    })
    .then(post => {
        ['post-title', 'post-content', 'post-author', 'post-date'].forEach(id => {
            document.getElementById(id).value = '';
        });
        return loadPosts().then(() => showStatus('Post "' + post.title + '" added.'));
    })
    .catch(error => showStatus(error.message, true));
}

// Function to send a PUT request to the API with the edited fields of a post
function updatePost(postId, fields) {
    var baseUrl = getBaseUrl();
    var changes = {};
    Object.keys(fields).forEach(name => {
        changes[name] = fields[name].value;
    });

    requestJson(baseUrl + '/posts/' + postId, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(changes)
    })
    .then(post => {
        return loadPosts().then(() => showStatus('Post "' + post.title + '" updated.'));
    })
    .catch(error => showStatus(error.message, true));
}

// Function to send a DELETE request to the API to delete a post
function deletePost(postId) {
    var baseUrl = getBaseUrl();
    requestJson(baseUrl + '/posts/' + postId, { method: 'DELETE' })
        .then(result => {
            return loadPosts().then(() => showStatus(result.message));
        })
        .catch(error => showStatus(error.message, true));
}
