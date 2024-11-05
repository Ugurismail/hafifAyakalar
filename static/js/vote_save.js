// static/js/vote_save.js

document.addEventListener('DOMContentLoaded', function() {
    // Function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                // Check if this cookie string begins with the name we want
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // **Voting Functionality**
    const voteButtons = document.querySelectorAll('.vote-btn');

    voteButtons.forEach(function(voteButton) {
        voteButton.addEventListener('click', function(event) {
            event.preventDefault();

            const contentType = this.getAttribute('data-content-type');
            const objectId = this.getAttribute('data-object-id');
            const value = parseInt(this.getAttribute('data-value'));

            fetch('/vote/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({
                    'content_type': contentType,
                    'object_id': objectId,
                    'value': value
                })
            })
            .then(response => {
                if (!response.ok) {
                    // For debugging purposes, you can get the error text
                    return response.text().then(text => { throw new Error(text) });
                }
                return response.json();
            })
            .then(data => {
                if (data.upvotes !== undefined && data.downvotes !== undefined) {
                    // Update the vote counts in the UI
                    if (contentType === 'question') {
                        document.getElementById('question-upvotes').innerText = data.upvotes;
                        document.getElementById('question-downvotes').innerText = data.downvotes;

                        // Update vote button styles
                        const upvoteButton = document.querySelector(`.vote-btn[data-content-type="question"][data-object-id="${objectId}"][data-value="1"]`);
                        const downvoteButton = document.querySelector(`.vote-btn[data-content-type="question"][data-object-id="${objectId}"][data-value="-1"]`);
                        updateVoteButtonStyles(upvoteButton, downvoteButton, data.user_vote_value);

                    } else if (contentType === 'answer') {
                        document.getElementById(`answer-upvotes-${objectId}`).innerText = data.upvotes;
                        document.getElementById(`answer-downvotes-${objectId}`).innerText = data.downvotes;

                        // Update vote button styles
                        const upvoteButton = document.querySelector(`.vote-btn[data-content-type="answer"][data-object-id="${objectId}"][data-value="1"]`);
                        const downvoteButton = document.querySelector(`.vote-btn[data-content-type="answer"][data-object-id="${objectId}"][data-value="-1"]`);
                        updateVoteButtonStyles(upvoteButton, downvoteButton, data.user_vote_value);
                    }
                } else if (data.message) {
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });

    // **Save Functionality**
    const saveButtons = document.querySelectorAll('.save-btn');

    saveButtons.forEach(function(saveButton) {
        saveButton.addEventListener('click', function(event) {
            event.preventDefault();

            const contentType = this.getAttribute('data-content-type');
            const objectId = this.getAttribute('data-object-id');
            const icon = this.querySelector('i');
            const saveCountSpan = this.nextElementSibling; // Assuming the save count is next to the button

            fetch('/save-item/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({
                    'content_type': contentType,
                    'object_id': objectId
                })
            })
            .then(response => {
                if (!response.ok) {
                    // For debugging purposes, you can get the error text
                    return response.text().then(text => { throw new Error(text) });
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'saved') {
                    // Update the icon to indicate saved
                    icon.classList.remove('bi-bookmark');
                    icon.classList.add('bi-bookmark-fill');
                } else if (data.status === 'removed') {
                    // Update the icon to indicate not saved
                    icon.classList.remove('bi-bookmark-fill');
                    icon.classList.add('bi-bookmark');
                }
                if (data.save_count !== undefined) {
                    saveCountSpan.innerText = data.save_count;
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
    function updateVoteButtonStyles(upvoteButton, downvoteButton, userVoteValue) {
        // Remove any existing 'voted' classes
        upvoteButton.classList.remove('voted-up');
        downvoteButton.classList.remove('voted-down');
    
        // Add the appropriate class based on user vote
        if (userVoteValue === 1 || userVoteValue === "1") {
            upvoteButton.classList.add('voted-up');
        } else if (userVoteValue === -1 || userVoteValue === "-1") {
            downvoteButton.classList.add('voted-down');
        }
    }
});
