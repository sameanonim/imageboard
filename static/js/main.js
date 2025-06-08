// Функция для обработки загрузки файлов
function handleFileUpload(input, maxFiles, maxSize) {
    const files = input.files;
    const fileList = document.createElement('ul');
    fileList.className = 'file-list';
    
    // Очищаем предыдущий список
    const existingList = input.parentElement.querySelector('.file-list');
    if (existingList) {
        existingList.remove();
    }
    
    if (files.length > maxFiles) {
        alert(`Максимальное количество файлов: ${maxFiles}`);
        input.value = '';
        return;
    }
    
    for (let file of files) {
        if (file.size > maxSize) {
            alert(`Файл ${file.name} слишком большой. Максимальный размер: ${maxSize / 1024 / 1024}MB`);
            input.value = '';
            return;
        }
        
        const li = document.createElement('li');
        li.textContent = `${file.name} (${(file.size / 1024).toFixed(1)}KB)`;
        fileList.appendChild(li);
    }
    
    input.parentElement.appendChild(fileList);
}

// Функция для предпросмотра изображений
function previewImages(input) {
    const preview = document.createElement('div');
    preview.className = 'image-preview';
    
    // Очищаем предыдущий предпросмотр
    const existingPreview = input.parentElement.querySelector('.image-preview');
    if (existingPreview) {
        existingPreview.remove();
    }
    
    if (input.files) {
        for (let file of input.files) {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    preview.appendChild(img);
                }
                reader.readAsDataURL(file);
            }
        }
    }
    
    input.parentElement.appendChild(preview);
}

// Функция для обработки цитирования
function handleQuote(postId) {
    const post = document.querySelector(`#post-${postId}`);
    if (!post) return;
    
    const content = post.querySelector('.post-text').textContent;
    const textarea = document.querySelector('#content');
    if (!textarea) return;
    
    textarea.value += `>>${postId}\n${content}\n\n`;
    textarea.focus();
}

// Функция для обработки жалоб
async function handleReport(postId) {
    if (!confirm('Отправить жалобу на этот пост?')) return;
    
    try {
        const response = await fetch(`/api/posts/${postId}/report`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        if (data.success) {
            alert('Жалоба отправлена');
        } else {
            alert('Ошибка при отправке жалобы');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при отправке жалобы');
    }
}

// Функция для скрытия треда
function hideThread(threadId) {
    const hiddenThreads = JSON.parse(localStorage.getItem('hiddenThreads') || '[]');
    if (!hiddenThreads.includes(threadId)) {
        hiddenThreads.push(threadId);
        localStorage.setItem('hiddenThreads', JSON.stringify(hiddenThreads));
        document.querySelector(`[data-thread-id="${threadId}"]`).closest('.thread').style.display = 'none';
    }
}

// Функция для скрытия поста
function hidePost(postId) {
    const hiddenPosts = JSON.parse(localStorage.getItem('hiddenPosts') || '[]');
    if (!hiddenPosts.includes(postId)) {
        hiddenPosts.push(postId);
        localStorage.setItem('hiddenPosts', JSON.stringify(hiddenPosts));
        document.querySelector(`[data-post-id="${postId}"]`).closest('.post').style.display = 'none';
    }
}

// Функция для сохранения черновика
function saveDraft(threadId) {
    const name = document.querySelector('input[name="name"]').value;
    const content = document.querySelector('textarea[name="content"]').value;
    const draft = { name, content };
    localStorage.setItem(`draft_${threadId}`, JSON.stringify(draft));
    alert('Черновик сохранен');
}

// Функция для восстановления черновика
function restoreDraft(threadId) {
    const draft = JSON.parse(localStorage.getItem(`draft_${threadId}`));
    if (draft) {
        document.querySelector('input[name="name"]').value = draft.name;
        document.querySelector('textarea[name="content"]').value = draft.content;
    }
}

// Функции для быстрого ответа
function initQuickReply() {
    const form = document.getElementById('quick-reply-form');
    const expandButton = document.getElementById('expand-quick-reply');
    const cancelButton = document.getElementById('cancel-quick-reply');
    const content = document.querySelector('.quick-reply-content');
    const textarea = form.querySelector('textarea');
    const fileInput = form.querySelector('input[type="file"]');
    const filePreview = form.querySelector('.file-preview');

    // Обработчик разворачивания формы
    expandButton.addEventListener('click', () => {
        content.style.display = 'block';
        expandButton.style.display = 'none';
        textarea.focus();
    });

    // Обработчик сворачивания формы
    cancelButton.addEventListener('click', () => {
        content.style.display = 'none';
        expandButton.style.display = 'block';
        form.reset();
        filePreview.innerHTML = '';
    });

    // Обработчик загрузки файлов
    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        filePreview.innerHTML = '';

        files.forEach(file => {
            const reader = new FileReader();
            const preview = document.createElement('div');
            preview.className = 'preview-item';

            reader.onload = (e) => {
                if (file.type.startsWith('video/')) {
                    preview.innerHTML = `
                        <video src="${e.target.result}" class="preview-media"></video>
                        <span class="preview-name">${file.name}</span>
                    `;
                } else {
                    preview.innerHTML = `
                        <img src="${e.target.result}" class="preview-media">
                        <span class="preview-name">${file.name}</span>
                    `;
                }
            };

            reader.readAsDataURL(file);
            filePreview.appendChild(preview);
        });
    });

    // Обработчик отправки формы
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                // Очищаем форму
                form.reset();
                filePreview.innerHTML = '';
                content.style.display = 'none';
                expandButton.style.display = 'block';

                // Обновляем страницу
                window.location.reload();
            } else {
                const error = await response.json();
                alert(error.message || 'Ошибка при отправке ответа');
            }
        } catch (error) {
            alert('Ошибка при отправке ответа');
        }
    });
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Обработка загрузки файлов
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const maxFiles = parseInt(this.getAttribute('max')) || 4;
            const maxSize = parseInt(this.getAttribute('data-max-size')) || 8 * 1024 * 1024;
            handleFileUpload(this, maxFiles, maxSize);
            previewImages(this);
        });
    });
    
    // Обработка кнопок цитирования
    document.querySelectorAll('.quote-btn').forEach(button => {
        button.addEventListener('click', function() {
            handleQuote(this.dataset.postId);
        });
    });
    
    // Обработка кнопок жалоб
    document.querySelectorAll('.report-btn').forEach(button => {
        button.addEventListener('click', function() {
            handleReport(this.dataset.postId);
        });
    });
    
    // Автоматическое обновление тредов
    const threadContainer = document.querySelector('.posts-container');
    if (threadContainer) {
        const threadId = threadContainer.dataset.threadId;
        const boardName = threadContainer.dataset.boardName;
        
        setInterval(async () => {
            try {
                const response = await fetch(`/api/boards/${boardName}/threads/${threadId}`);
                const data = await response.json();
                
                // Обновляем посты
                const posts = data.posts;
                const lastPostId = parseInt(threadContainer.dataset.lastPostId) || 0;
                
                posts.forEach(post => {
                    if (post.id > lastPostId) {
                        // Добавляем новый пост
                        const postElement = createPostElement(post);
                        threadContainer.appendChild(postElement);
                        threadContainer.dataset.lastPostId = post.id;
                    }
                });
            } catch (error) {
                console.error('Ошибка при обновлении треда:', error);
            }
        }, 30000); // Обновляем каждые 30 секунд
    }

    // При загрузке страницы проверяем localStorage и скрываем элементы
    const hiddenThreads = JSON.parse(localStorage.getItem('hiddenThreads') || '[]');
    const hiddenPosts = JSON.parse(localStorage.getItem('hiddenPosts') || '[]');

    hiddenThreads.forEach(threadId => {
        const threadElement = document.querySelector(`[data-thread-id="${threadId}"]`);
        if (threadElement) {
            threadElement.closest('.thread').style.display = 'none';
        }
    });

    hiddenPosts.forEach(postId => {
        const postElement = document.querySelector(`[data-post-id="${postId}"]`);
        if (postElement) {
            postElement.closest('.post').style.display = 'none';
        }
    });

    // Добавляем обработчики для кнопок скрытия
    document.querySelectorAll('.hide-thread').forEach(button => {
        button.addEventListener('click', () => hideThread(button.dataset.threadId));
    });

    document.querySelectorAll('.hide-post').forEach(button => {
        button.addEventListener('click', () => hidePost(button.dataset.postId));
    });

    // При загрузке страницы проверяем наличие черновиков
    const threadId = window.location.pathname.split('/').pop();
    const saveDraftButton = document.getElementById('save-draft');
    if (saveDraftButton) {
        saveDraftButton.addEventListener('click', () => saveDraft(threadId));
    }
    restoreDraft(threadId);

    // Инициализация быстрого ответа
    if (document.getElementById('quick-reply-form')) {
        initQuickReply();
    }
});

// Функция для создания элемента поста
function createPostElement(post) {
    const div = document.createElement('div');
    div.className = 'post';
    div.id = `post-${post.id}`;
    
    div.innerHTML = `
        <div class="post-header">
            <span class="post-number">№${post.id}</span>
            ${post.name ? `<span class="post-name">${post.name}</span>` : ''}
            <span class="post-date">${new Date(post.created_at).toLocaleString()}</span>
        </div>
        <div class="post-content">
            ${post.files.length > 0 ? `
                <div class="post-files">
                    ${post.files.map(file => `
                        <div class="file">
                            <a href="/static/uploads/${file.filename}" target="_blank" class="file-link">
                                <img src="/static/uploads/${file.filename}" 
                                     alt="${file.original_filename}"
                                     loading="lazy">
                            </a>
                            <div class="file-info">
                                <span class="file-name">${file.original_filename}</span>
                                <span class="file-size">${(file.file_size / 1024).toFixed(1)}KB</span>
                                ${file.width && file.height ? 
                                    `<span class="file-dimensions">${file.width}x${file.height}</span>` : 
                                    ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            <div class="post-text">${post.content}</div>
        </div>
        <div class="post-actions">
            <a href="#post-${post.id}" class="post-link">Ссылка</a>
            <button class="quote-btn" data-post-id="${post.id}">Цитировать</button>
            <button class="report-btn" data-post-id="${post.id}">Пожаловаться</button>
        </div>
    `;
    
    // Добавляем обработчики событий
    div.querySelector('.quote-btn').addEventListener('click', function() {
        handleQuote(this.dataset.postId);
    });
    
    div.querySelector('.report-btn').addEventListener('click', function() {
        handleReport(this.dataset.postId);
    });
    
    return div;
} 