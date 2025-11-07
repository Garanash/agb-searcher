// Test assistant editing in browser console
// Run this in browser console on the settings page

console.log('=== ТЕСТ РЕДАКТИРОВАНИЯ ПОМОЩНИКОВ ===');

// 1. Проверяем, что помощники загружены
console.log('1. Загружаем помощников...');
fetch('/api/assistants')
  .then(response => response.json())
  .then(assistants => {
    console.log('Помощники:', assistants);
    
    if (assistants.length > 0) {
      const assistant = assistants[0];
      console.log('2. Тестируем обновление помощника:', assistant.name);
      
      // Тестируем обновление
      const updateData = {
        name: 'Тестовый помощник ' + new Date().getTime(),
        description: 'Обновленное описание для теста',
        temperature: '0.8'
      };
      
      console.log('Данные для обновления:', updateData);
      
      fetch(`/api/assistants/${assistant.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
      })
      .then(response => {
        console.log('Статус ответа:', response.status);
        return response.json();
      })
      .then(updatedAssistant => {
        console.log('✅ Помощник обновлен:', updatedAssistant);
      })
      .catch(error => {
        console.error('❌ Ошибка при обновлении:', error);
      });
    } else {
      console.log('Нет помощников для тестирования');
    }
  })
  .catch(error => {
    console.error('❌ Ошибка при загрузке помощников:', error);
  });
