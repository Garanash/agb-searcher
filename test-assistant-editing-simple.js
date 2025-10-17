#!/usr/bin/env node

// Simple test script for assistant editing
// Run with: node test-assistant-editing-simple.js

const https = require('https');
const http = require('http');

const API_URL = 'http://localhost:8000';

function makeRequest(url, method = 'GET', data = null) {
  return new Promise((resolve, reject) => {
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    const req = http.request(url, options, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(body);
          resolve({ status: res.statusCode, data: json });
        } catch (e) {
          resolve({ status: res.statusCode, data: body });
        }
      });
    });

    req.on('error', reject);
    
    if (data) {
      req.write(JSON.stringify(data));
    }
    
    req.end();
  });
}

async function testAssistantEditing() {
  console.log('🧪 Тестирование редактирования ассистентов...\n');

  try {
    // 1. Получаем список ассистентов
    console.log('1️⃣ Получаем список ассистентов...');
    const assistantsResponse = await makeRequest(`${API_URL}/assistants`);
    
    if (assistantsResponse.status !== 200) {
      throw new Error(`Ошибка получения ассистентов: ${assistantsResponse.status}`);
    }
    
    const assistants = assistantsResponse.data;
    console.log(`✅ Найдено ассистентов: ${assistants.length}`);
    
    if (assistants.length === 0) {
      console.log('❌ Нет ассистентов для тестирования');
      return;
    }

    // 2. Выбираем первого ассистента для тестирования
    const assistant = assistants[0];
    console.log(`\n2️⃣ Тестируем ассистента: "${assistant.name}" (ID: ${assistant.id})`);

    // 3. Подготавливаем данные для обновления
    const updateData = {
      name: `Тестовый ${assistant.name} ${Date.now()}`,
      description: `Обновленное описание для теста в ${new Date().toLocaleString()}`,
      temperature: '0.9',
      max_tokens: 1500
    };

    console.log('3️⃣ Данные для обновления:');
    console.log(JSON.stringify(updateData, null, 2));

    // 4. Обновляем ассистента
    console.log('\n4️⃣ Отправляем запрос на обновление...');
    const updateResponse = await makeRequest(
      `${API_URL}/assistants/${assistant.id}`,
      'PUT',
      updateData
    );

    if (updateResponse.status !== 200) {
      throw new Error(`Ошибка обновления: ${updateResponse.status} - ${JSON.stringify(updateResponse.data)}`);
    }

    console.log('✅ Ассистент успешно обновлен!');
    console.log('\n5️⃣ Результат обновления:');
    console.log(`   Название: ${updateResponse.data.name}`);
    console.log(`   Описание: ${updateResponse.data.description}`);
    console.log(`   Temperature: ${updateResponse.data.temperature}`);
    console.log(`   Max tokens: ${updateResponse.data.max_tokens}`);
    console.log(`   Обновлено: ${updateResponse.data.updated_at}`);

    // 5. Проверяем, что изменения сохранились
    console.log('\n6️⃣ Проверяем сохранение изменений...');
    const verifyResponse = await makeRequest(`${API_URL}/assistants/${assistant.id}`);
    
    if (verifyResponse.status !== 200) {
      throw new Error(`Ошибка проверки: ${verifyResponse.status}`);
    }

    const updatedAssistant = verifyResponse.data;
    if (updatedAssistant.name === updateData.name) {
      console.log('✅ Изменения успешно сохранены в базе данных!');
    } else {
      console.log('❌ Изменения не сохранились');
    }

    console.log('\n🎉 Тест редактирования ассистентов завершен успешно!');
    console.log('\n📋 Следующие шаги:');
    console.log('   1. Откройте http://188.225.56.200:3000/settings');
    console.log('   2. Перейдите на вкладку "Помощники"');
    console.log('   3. Попробуйте отредактировать ассистента через интерфейс');
    console.log('   4. Проверьте, что изменения сохраняются');

  } catch (error) {
    console.error('❌ Ошибка при тестировании:', error.message);
    console.log('\n🔧 Возможные решения:');
    console.log('   1. Убедитесь, что приложение запущено: docker-compose ps');
    console.log('   2. Перезапустите backend: docker-compose restart backend');
    console.log('   3. Проверьте логи: docker-compose logs backend');
  }
}

// Запускаем тест
testAssistantEditing();
