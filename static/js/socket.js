// Инициализация Socket.IO
const socket = io({
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    reconnectionAttempts: 5,
    timeout: 20000,
    autoConnect: true,
    transports: ['websocket', 'polling']
});

// Обработка подключения
socket.on('connect', () => {
    console.log('Connected to server');
    showNotification('Подключено к серверу', 'success');
    
    // Присоединяемся к треду, если мы на странице треда
    if (currentThreadId) {
        socket.emit('join_thread', { thread_id: currentThreadId });
    }
});

// Обработка отключения
socket.on('disconnect', (reason) => {
    console.log('Disconnected from server:', reason);
    showNotification('Отключено от сервера', 'error');
    
    // Если отключение произошло из-за ошибки сервера, пробуем переподключиться
    if (reason === 'io server disconnect') {
        socket.connect();
    }
});

// Обработка ошибок
socket.on('error', (data) => {
    console.error('Socket error:', data);
    showNotification(data.message || 'Ошибка соединения', 'error');
});

// Обработка ошибки подключения
socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
    showNotification('Ошибка подключения к серверу', 'error');
});

// Обработка успешного переподключения
socket.on('reconnect', (attemptNumber) => {
    console.log('Reconnected after', attemptNumber, 'attempts');
    showNotification('Переподключено к серверу', 'success');
    
    // Присоединяемся к треду после переподключения
    if (currentThreadId) {
        socket.emit('join_thread', { thread_id: currentThreadId });
    }
});

// Обработка неудачного переподключения
socket.on('reconnect_failed', () => {
    console.error('Failed to reconnect');
    showNotification('Не удалось переподключиться к серверу', 'error');
});

// Обработка новых постов
socket.on('new_post', (data) => {
    console.log('New post:', data);
    if (data.thread_id === currentThreadId) {
        appendPost(data);
    }
    showNotification(`Новый пост от ${data.user}`, 'info');
});

// Обработка новых ответов
socket.on('new_reply', (data) => {
    console.log('New reply:', data);
    if (data.thread_id === currentThreadId) {
        appendReply(data);
    }
    showNotification(`Новый ответ от ${data.user}`, 'info');
});

// Обработка блокировки треда
socket.on('thread_locked', (data) => {
    console.log('Thread locked:', data);
    if (data.thread_id === currentThreadId) {
        updateThreadStatus('locked');
    }
    showNotification(
        `Тред заблокирован модератором ${data.locked_by}`,
        'warning'
    );
});

// Обработка разблокировки треда
socket.on('thread_unlocked', (data) => {
    console.log('Thread unlocked:', data);
    if (data.thread_id === currentThreadId) {
        updateThreadStatus('unlocked');
    }
    showNotification(
        `Тред разблокирован модератором ${data.unlocked_by}`,
        'success'
    );
});

// Обработка удаления поста
socket.on('post_deleted', (data) => {
    console.log('Post deleted:', data);
    if (data.thread_id === currentThreadId) {
        removePost(data.post_id);
    }
    showNotification('Пост удален модератором', 'warning');
});

// Обработка достижений
socket.on('achievement', (data) => {
    console.log('Achievement:', data);
    showAchievement(data);
});

// Функция отображения уведомления
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    // Добавление уведомления в контейнер
    const container = document.getElementById('notifications') ||
        createNotificationContainer();
    container.appendChild(notification);

    // Анимация появления
    requestAnimationFrame(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateY(0)';
    });

    // Автоматическое удаление
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-20px)';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Создание контейнера для уведомлений
function createNotificationContainer() {
    const container = document.createElement('div');
    container.id = 'notifications';
    document.body.appendChild(container);
    return container;
}

// Функция добавления нового поста
function appendPost(data) {
    const post = createPostElement(data);
    const container = document.querySelector('.posts-container');
    container.appendChild(post);

    // Анимация появления
    requestAnimationFrame(() => {
        post.style.opacity = '1';
        post.style.transform = 'translateY(0)';
    });

    // Прокрутка к новому посту
    post.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Функция добавления нового ответа
function appendReply(data) {
    const reply = createReplyElement(data);
    const parent = document.querySelector(`#post-${data.reply_to_id}`);
    if (parent) {
        const replies = parent.querySelector('.replies') ||
            createRepliesContainer(parent);
        replies.appendChild(reply);

        // Анимация появления
        requestAnimationFrame(() => {
            reply.style.opacity = '1';
            reply.style.transform = 'translateX(0)';
        });
    }
}

// Создание контейнера для ответов
function createRepliesContainer(parent) {
    const container = document.createElement('div');
    container.className = 'replies';
    parent.appendChild(container);
    return container;
}

// Функция обновления статуса треда
function updateThreadStatus(status) {
    const thread = document.querySelector('.thread');
    if (thread) {
        thread.dataset.status = status;
        const statusElement = thread.querySelector('.thread-status');
        if (statusElement) {
            statusElement.textContent = status === 'locked' ? '🔒' : '🔓';
        }
    }
}

// Функция удаления поста
function removePost(postId) {
    const post = document.querySelector(`#post-${postId}`);
    if (post) {
        // Анимация удаления
        post.style.opacity = '0';
        post.style.transform = 'scale(0.8)';
        setTimeout(() => post.remove(), 300);
    }
}

// Функция отображения достижения
function showAchievement(data) {
    const achievement = document.createElement('div');
    achievement.className = 'achievement';
    achievement.innerHTML = `
        <div class="achievement-icon">${data.icon}</div>
        <div class="achievement-content">
            <div class="achievement-name">${data.name}</div>
            <div class="achievement-description">${data.description}</div>
        </div>
    `;

    // Добавление достижения в контейнер
    const container = document.getElementById('achievements') ||
        createAchievementContainer();
    container.appendChild(achievement);

    // Анимация появления
    requestAnimationFrame(() => {
        achievement.style.opacity = '1';
        achievement.style.transform = 'translateX(0)';
    });

    // Автоматическое удаление
    setTimeout(() => {
        achievement.style.opacity = '0';
        achievement.style.transform = 'translateX(100%)';
        setTimeout(() => achievement.remove(), 300);
    }, 5000);
}

// Создание контейнера для достижений
function createAchievementContainer() {
    const container = document.createElement('div');
    container.id = 'achievements';
    document.body.appendChild(container);
    return container;
}

// Функция создания элемента поста
function createPostElement(data) {
    const post = document.createElement('div');
    post.id = `post-${data.post_id}`;
    post.className = 'post';
    post.style.opacity = '0';
    post.style.transform = 'translateY(20px)';
    post.style.transition = 'opacity 0.3s, transform 0.3s';

    post.innerHTML = `
        <div class="post-header">
            <span class="post-user">${data.user}</span>
            <span class="post-time">${formatDate(data.created_at)}</span>
        </div>
        <div class="post-content">${data.content}</div>
    `;

    return post;
}

// Функция создания элемента ответа
function createReplyElement(data) {
    const reply = document.createElement('div');
    reply.id = `reply-${data.post_id}`;
    reply.className = 'reply';
    reply.style.opacity = '0';
    reply.style.transform = 'translateX(20px)';
    reply.style.transition = 'opacity 0.3s, transform 0.3s';

    reply.innerHTML = `
        <div class="reply-header">
            <span class="reply-user">${data.user}</span>
            <span class="reply-time">${formatDate(data.created_at)}</span>
        </div>
        <div class="reply-content">${data.content}</div>
    `;

    return reply;
}

// Функция форматирования даты
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Выход из треда при уходе со страницы
window.addEventListener('beforeunload', () => {
    if (currentThreadId) {
        socket.emit('leave_thread', { thread_id: currentThreadId });
    }
}); 