// Função para calcular a idade com base na data de nascimento
function calculateAge(dob) {
  const birthDate = new Date(dob);
  const today = new Date();
  let age = today.getFullYear() - birthDate.getFullYear();
  const month = today.getMonth() - birthDate.getMonth();
  if (month < 0 || (month === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  return age;
}

// Função para salvar os dados no Local Storage
function saveUserData(name, dob, age) {
  const userData = { name, dob, age };
  localStorage.setItem('userData', JSON.stringify(userData));
}

// Função para carregar os dados salvos do Local Storage
function loadUserData() {
  const userData = localStorage.getItem('userData');
  return userData ? JSON.parse(userData) : null;
}

// Função para exibir os dados cadastrados
function displayUserData() {
  const userData = loadUserData();
  if (userData) {
    document.getElementById('displayName').textContent = `Nome: ${userData.name}`;
    document.getElementById('displayAge').textContent = `Idade: ${userData.age} anos`;
    document.getElementById('userData').style.display = 'block';
    document.getElementById('editButton').style.display = 'inline';
    document.getElementById('deleteButton').style.display = 'inline';
  }
}
window.addEventListener('load', displayUserData);//adcicionado

// Função para limpar o formulário
function clearForm() {
  document.getElementById('name').value = '';
  document.getElementById('dob').value = '';
}

// Evento de envio do formulário
document.getElementById('userForm').addEventListener('submit', function (e) {
  e.preventDefault();
  const name = document.getElementById('name').value;
  const dob = document.getElementById('dob').value;
  const age = calculateAge(dob);

  saveUserData(name, dob, age);
  displayUserData();
  clearForm();
});

// Evento para editar os dados
document.getElementById('editButton').addEventListener('click', function () {
  const userData = loadUserData();
  if (userData) {
    document.getElementById('name').value = userData.name;
    document.getElementById('dob').value = userData.dob;
  }
});

// Evento para excluir os dados
document.getElementById('deleteButton').addEventListener('click', function () {
  localStorage.removeItem('userData');
  document.getElementById('userData').style.display = 'none';
  document.getElementById('editButton').style.display = 'none';
  document.getElementById('deleteButton').style.display = 'none';
});