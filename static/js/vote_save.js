document.addEventListener('DOMContentLoaded', function() {
    // Function to get CSRF token from cookies
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
    const csrfToken = getCookie('csrftoken');

    // Voting buttons
    const voteButtons = document.querySelectorAll('.vote-btn');

    voteButtons.forEach(btn => {
        btn.addEventListener('click', function(event) {
            event.preventDefault();
            const contentType = this.getAttribute('data-content-type');
            const objectId = this.getAttribute('data-object-id');
            const value = this.getAttribute('data-value');

            fetch('/vote/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: content_type=${contentType}&object_id=${objectId}&value=${value},
            })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text) });
                }
                return response.json();
            })
            .then(data => {
                if (data.upvotes !== undefined && data.downvotes !== undefined) {
                    if (contentType === 'question') {
                        document.getElementById('question-upvotes').innerText = data.upvotes;
                        document.getElementById('question-downvotes').innerText = data.downvotes;
                    } else if (contentType === 'answer') {
                        document.getElementById(answer-upvotes-${objectId}).innerText = data.upvotes;
                        document.getElementById(answer-downvotes-${objectId}).innerText = data.downvotes;
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });

   // Save buttons
    const saveButtons = document.querySelectorAll('.save-btn');

    saveButtons.forEach(btn => {
        btn.addEventListener('click', function(event) {
            event.preventDefault();
            const contentType = this.getAttribute('data-content-type');
            const objectId = this.getAttribute('data-object-id');
            const icon = this.querySelector('i');
            const saveCountSpan = this.nextElementSibling; // Kaydetme sayısını gösteren <span>

            // Debugging için konsol logları
            console.log('Kaydetme butonuna tıklandı');
            console.log('Content Type:', contentType);
            console.log('Object ID:', objectId);
            console.log('Icon:', icon);
            console.log('Save Count Span:', saveCountSpan);

            fetch('/save-item/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: content_type=${contentType}&object_id=${objectId},
            })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text) });
                }
                return response.json();
            })
            .then(data => {
                console.log('Sunucudan dönen veri:', data);
                if (data.status === 'saved') {
                    icon.classList.remove('bi-bookmark');
                    icon.classList.add('bi-bookmark-fill');
                } else if (data.status === 'removed') {
                    icon.classList.remove('bi-bookmark-fill');
                    icon.classList.add('bi-bookmark');
                }
                // Kaydetme sayısını güncelle
                if (data.save_count !== undefined) {
                    saveCountSpan.innerText = data.save_count;
                    console.log('Kaydetme sayısı güncellendi:', data.save_count);
                } else {
                    console.log('Sunucudan save_count değeri gelmedi.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
});