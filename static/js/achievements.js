function showAchievement(achievement) {
    const notification = document.createElement('div');
    notification.className = 'achievement-notification';
    
    const content = document.createElement('div');
    content.className = 'achievement-content';
    
    const icon = document.createElement('span');
    icon.className = 'achievement-icon';
    icon.textContent = achievement.icon;
    
    const text = document.createElement('div');
    text.className = 'achievement-text';
    
    const title = document.createElement('div');
    title.className = 'achievement-title';
    title.textContent = achievement.title;
    
    const description = document.createElement('div');
    description.className = 'achievement-description';
    description.textContent = achievement.description;
    
    text.appendChild(title);
    text.appendChild(description);
    
    content.appendChild(icon);
    content.appendChild(text);
    
    notification.appendChild(content);
    document.body.appendChild(notification);
    
    // Анимация появления
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Анимация исчезновения
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 500);
    }, 5000);
}

function showAchievements(achievements) {
    if (!achievements || !achievements.length) return;
    
    // Показываем достижения с задержкой
    achievements.forEach((achievement, index) => {
        setTimeout(() => {
            showAchievement(achievement);
        }, index * 1000);
    });
}

// Обработчик для отображения достижений при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    const achievementsData = document.getElementById('achievements-data');
    if (achievementsData) {
        const achievements = JSON.parse(achievementsData.textContent);
        showAchievements(achievements);
    }
}); 