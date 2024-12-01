document.addEventListener('DOMContentLoaded', function() {
    let selectedPost = null;

    document.getElementById('fetch-posts').addEventListener('click', fetchPosts);
    document.getElementById('convert').addEventListener('click', convertPost);
    document.querySelector('.close').addEventListener('click', closeModal);
    document.getElementById('select-post-button').addEventListener('click', selectPostFromModal);

    async function fetchPosts() {
        const loading = document.getElementById('loading');
        const error = document.getElementById('error');
        const gallery = document.getElementById('gallery');

        loading.style.display = 'block';
        error.style.display = 'none';
        gallery.innerHTML = '';

        try {
            const response = await fetch('/fetch_posts', { method: 'POST' });
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            data.posts.forEach(post => {
                const postElement = document.createElement('div');
                postElement.className = 'post';

                let imagesHtml = '<div class="post-images">';
                post.media_urls.forEach(url => {
                    imagesHtml += `<img src="${url}" alt="Instagram post" onerror="this.onerror=null; this.src='/static/placeholder.png';">`;
                });
                imagesHtml += '</div>';

                postElement.innerHTML = `
                    ${imagesHtml}
                    <p>${post.caption.substring(0, 50)}...</p>
                `;
                postElement.addEventListener('click', () => openModal(post));
                gallery.appendChild(postElement);
            });

            document.getElementById('conversion-form').style.display = 'block';
        } catch (err) {
            error.textContent = `Error: ${err.message}`;
            error.style.display = 'block';
        } finally {
            loading.style.display = 'none';
        }
    }

    function openModal(post) {
        const modal = document.getElementById('post-modal');
        const modalContent = document.getElementById('modal-post-content');

        let imagesHtml = '<div class="post-images">';
        post.media_urls.forEach(url => {
            imagesHtml += `<img src="${url}" alt="Instagram post" onerror="this.onerror=null; this.src='/static/placeholder.png';">`;
        });
        imagesHtml += '</div>';

        modalContent.innerHTML = `
            ${imagesHtml}
            <p>${post.caption}</p>
        `;
        modal.style.display = 'block';
        selectedPost = post;
    }

    function closeModal() {
        document.getElementById('post-modal').style.display = 'none';
    }

    function selectPostFromModal() {
        if (selectedPost) {
            alert(`Post selected for conversion: ${selectedPost.caption.substring(0, 50)}...`);
            closeModal();
        }
    }

    async function convertPost() {
        if (!selectedPost) {
            alert('Please select a post to convert first.');
            return;
        }

        const targetPlatform = document.getElementById('target-platform').value;
        const conversionResult = document.getElementById('conversion-result');
        const basicConvertedContent = document.getElementById('basic-converted-content');
        const ragConvertedContent = document.getElementById('rag-converted-content');

        try {
            const response = await fetch('/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    caption: selectedPost.caption,
                    targetPlatform: targetPlatform,
                    hasImage: selectedPost.media_urls.length > 0,
                }),
            });

            const data = await response.json();
            basicConvertedContent.textContent = data.basicConvertedPost;
            ragConvertedContent.textContent = data.ragConvertedPost;
            conversionResult.style.display = 'block';
        } catch (err) {
            alert(`Error converting post: ${err.message}`);
        }
    }
});