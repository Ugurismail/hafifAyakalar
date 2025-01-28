// static/js/vote_save.js

document.addEventListener('DOMContentLoaded', function() {
    // CSRF token'ını al
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // **Oylama İşlevselliği** (Upvote / Downvote)
    document.addEventListener('click', function(event) {
        if (event.target.matches('.vote-btn') || event.target.closest('.vote-btn')) {
            event.preventDefault();
            const voteButton = event.target.closest('.vote-btn');
            const contentType = voteButton.getAttribute('data-content-type');
            const objectId = voteButton.getAttribute('data-object-id');
            const value = parseInt(voteButton.getAttribute('data-value'));

            // FormData
            const formData = new FormData();
            formData.append('content_type', contentType);
            formData.append('object_id', objectId);
            formData.append('value', value);

            fetch('/vote/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken
                },
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text); });
                }
                return response.json();
            })
            .then(data => {
                if (data.upvotes !== undefined && data.downvotes !== undefined) {
                    if (contentType === 'question') {
                        // Soru up/down sayıları
                        document.getElementById('question-upvotes').innerText = data.upvotes;
                        document.getElementById('question-downvotes').innerText = data.downvotes;

                        const upvoteButton = document.querySelector(`.vote-btn[data-content-type="question"][data-object-id="${objectId}"][data-value="1"]`);
                        const downvoteButton = document.querySelector(`.vote-btn[data-content-type="question"][data-object-id="${objectId}"][data-value="-1"]`);
                        updateVoteButtonStyles(upvoteButton, downvoteButton, data.user_vote_value);

                    } else if (contentType === 'answer') {
                        // Yanıt up/down sayıları
                        document.getElementById(`answer-upvotes-${objectId}`).innerText = data.upvotes;
                        document.getElementById(`answer-downvotes-${objectId}`).innerText = data.downvotes;

                        const upvoteButton = document.querySelector(`.vote-btn[data-content-type="answer"][data-object-id="${objectId}"][data-value="1"]`);
                        const downvoteButton = document.querySelector(`.vote-btn[data-content-type="answer"][data-object-id="${objectId}"][data-value="-1"]`);
                        updateVoteButtonStyles(upvoteButton, downvoteButton, data.user_vote_value);
                    }
                } else if (data.message) {
                    alert(data.message);
                }
            })
            .catch(error => console.error('Error:', error));
        }
    });

    // **Kaydet / Kaydetmeyi Kaldır İşlevi** (Save / Unsave)
    document.addEventListener('click', function(event) {
        if (event.target.matches('.save-btn') || event.target.closest('.save-btn')) {
            event.preventDefault();
            const saveButton = event.target.closest('.save-btn');
            const contentType = saveButton.getAttribute('data-content-type');
            const objectId = saveButton.getAttribute('data-object-id');

            // FormData
            const formData = new FormData();
            formData.append('content_type', contentType);
            formData.append('object_id', objectId);

            fetch('/save-item/', {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken },
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text); });
                }
                return response.json();
            })
            .then(data => {
                // İkon veya metin güncellemesi
                const icon = saveButton.querySelector('i');
                if (data.status === 'saved') {
                    if (icon) {
                        icon.classList.remove('bi-bookmark');
                        icon.classList.add('bi-bookmark-fill');
                    }
                } else if (data.status === 'unsaved' || data.status === 'removed') {
                    if (icon) {
                        icon.classList.remove('bi-bookmark-fill');
                        icon.classList.add('bi-bookmark');
                    }
                }
                // Kaydet sayısı güncellemesi
                if (data.save_count !== undefined) {
                    const saveCountSpan = saveButton.nextElementSibling;
                    if (saveCountSpan) {
                        saveCountSpan.innerText = data.save_count;
                    }
                }
                // Profildeyse sayfa yenile
                if (window.location.href.includes('/profile/')) {
                    window.location.reload();
                }
            })
            .catch(error => console.error('Error:', error));
        }
    });

    // Oy butonlarının görünümünü güncelle
    function updateVoteButtonStyles(upvoteButton, downvoteButton, userVoteValue) {
        if (upvoteButton) upvoteButton.classList.remove('voted-up');
        if (downvoteButton) downvoteButton.classList.remove('voted-down');

        if (userVoteValue === 1 || userVoteValue === "1") {
            if (upvoteButton) upvoteButton.classList.add('voted-up');
        } else if (userVoteValue === -1 || userVoteValue === "-1") {
            if (downvoteButton) downvoteButton.classList.add('voted-down');
        }
    }
});
