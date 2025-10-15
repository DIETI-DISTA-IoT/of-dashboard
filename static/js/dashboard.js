function openTab(evt, tabId) {
      // Hide all tabs
      document.querySelectorAll(".tabcontent").forEach(tab => tab.style.display = "none");

      // Remove 'active' class from all tab buttons
      document.querySelectorAll(".tablink").forEach(btn => btn.classList.remove("active"));

      // Show the selected tab
      document.getElementById(tabId).style.display = "block";

      // Mark the clicked button as active
      evt.currentTarget.classList.add("active");
    }

window.addEventListener('DOMContentLoaded', (event) => {

  const configForm = document.getElementById("config-form");
  const produceAllButton = document.getElementById("produce-all");
  const consumeAllButton = document.getElementById("consume-all");
  const stopProduceAllButton = document.getElementById("stop-producing-all");
  const stopConsumeAllButton = document.getElementById("stop-consuming-all");
  const startWandbButton = document.getElementById("start-wandb");
  const stopWandbButton = document.getElementById("stop-wandb");
  const createVehiclesButton = document.getElementById("create-vehicles");
  const deleteVehiclesButton = document.getElementById("delete-vehicles");
  const startFederatedLearningButton = document.getElementById("start-federated-learning");
  const stopFederatedLearningButton = document.getElementById("stop-federated-learning");
  const startSecurityManagerButton = document.getElementById("start-security-manager");
  const stopSecurityManagerButton = document.getElementById("stop-security-manager");
  const startAutomaticAttacksButton = document.getElementById("start-automatic-attacks");
  const stopAutomaticAttacksButton = document.getElementById("stop-automatic-attacks");
  const startAttackButtons = Array.from(document.querySelectorAll('[id$="_start_attack"]'));
  const stopAttackButtons = Array.from(document.querySelectorAll('[id$="_end_attack"]'))
  const startPreconfAttackButton = document.getElementById("start-preconf-attack");
  const stopPreconfAttackButton = document.getElementById("stop-preconf-attack");
  const shutdownButton = document.getElementById("shutdown");
  const startExperimentButton = document.getElementById("start-experiment");
  const startMitigationButton = document.getElementById("start-mitigation");
  const stopMitigationButton = document.getElementById("stop-mitigation");

  var config = {};

  function updateConfigDict() {
        const formData = new FormData(configForm);
        config = {}; // reset

        // First handle all regular inputs (text, number, selects, checked checkboxes)
        formData.forEach((val, key) => {
            const keys = key.split('.');
            let curr = config;
            for (let i = 0; i < keys.length - 1; i++) {
                const k = keys[i];
                curr[k] = curr[k] || {};
                curr = curr[k];
            }
            curr[keys[keys.length - 1]] = val;
        });

        // Now explicitly handle ALL checkboxes (checked or not)
        const checkboxes = configForm.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => {
            const keys = cb.name.split('.');
            let curr = config;
            for (let i = 0; i < keys.length - 1; i++) {
                const k = keys[i];
                curr[k] = curr[k] || {};
                curr = curr[k];
            }
            curr[keys[keys.length - 1]] = cb.checked;
        });

    }

  configForm.addEventListener("submit", function(e) {
      e.preventDefault();
      updateConfigDict();
      alert("Configuration Saved!!");
      // TODO: send config dict to backend with fetch/axios
    });

    updateConfigDict();

  
  startAutomaticAttacksButton.addEventListener("click", function() {
      fetch("/start-automatic-attacks", {method: "POST"})
        .then(response => response.text())
        .then(data => console.log(data));
  });

  stopAutomaticAttacksButton.addEventListener("click", function() {
      fetch("/stop-automatic-attacks", {method: "POST"})
        .then(response => response.text())
        .then(data => console.log(data));
  });

  produceAllButton.addEventListener("click", function() {
      fetch("/produce-all", {method: "POST"})
        .then(response => response.text())
        .then(data => console.log(data));
  });

  consumeAllButton.addEventListener("click", function() {
      fetch("/consume-all", {method: "POST"})
        .then(response => response.text())
        .then(data => console.log(data));
  });

  stopProduceAllButton.addEventListener("click", function() {
      fetch("/stop-producing-all", {method: "POST"})
        .then(response => response.text())
        .then(data => console.log(data));
  });

  stopConsumeAllButton.addEventListener("click", function() {
      fetch("/stop-consuming-all", {method: "POST"})
        .then(response => response.text())
        .then(data => console.log(data));
  });

  startWandbButton.addEventListener("click", function() {
      fetch("/start-wandb", {method: "POST"})
        .then(response => response.text())
        .then(data => console.log(data));
  });

  stopWandbButton.addEventListener("click", function() {
      fetch("/stop-wandb", {method: "POST"})
        .then(response => response.text())
        .then(data => console.log(data));
  });

  createVehiclesButton.addEventListener("click", function() {
      fetch("/create-vehicles", {method: "POST"})
        .then(response => response.text())
        .then(data => console.log(data));
  });

  deleteVehiclesButton.addEventListener("click", function() {
      fetch("/delete-vehicles", {method: "POST"})
        .then(response => response.text())
        .then(data => console.log(data));
  });

  startFederatedLearningButton.addEventListener("click", function() {
      fetch("/start-federated-learning", {method: "POST"})
        .then(response => response.text())
        .then(data => console.log(data));
  });

  stopFederatedLearningButton.addEventListener("click", function() {
      fetch("/stop-federated-learning", {method: "POST"})
        .then(response => response.text())
        .then(data => console.log(data));
  });

  startSecurityManagerButton.addEventListener("click", function() {
      fetch("/start-security-manager", {method: "POST"})
        .then(response => response.text())
        .then(data => console.log(data));
  });

  stopSecurityManagerButton.addEventListener("click", function() {
      fetch("/stop-security-manager", {method: "POST"})
        .then(response => response.text())
        .then(data => console.log(data));
  });

  startPreconfAttackButton.addEventListener("click", function() {
      fetch("/start-preconf-attack", {method: "POST"})
        .then(response => response.text())
        .then(data => console.log(data));
  });

  stopPreconfAttackButton.addEventListener("click", function() {
      fetch("/stop-preconf-attack", {method: "POST"})
        .then(response => response.text())
        .then(data => console.log(data));
  });

  startAttackButtons.forEach(button => {
      button.addEventListener("click", function() {
          fetch("/start-attack", {
              method: "POST",
              headers: {
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify({ vehicle_name: button.id })
          })
          .then(response => response.text())
          .then(data => console.log(data));
      });
  });

  stopAttackButtons.forEach(button => {
      button.addEventListener("click", function() {
          fetch("/stop-attack", {
              method: "POST",
              headers: {
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify({ vehicle_name: button.id,
                                      origin: "MANUALLY"
                                    })
          })
          .then(response => response.text())
          .then(data => console.log(data));
      });
  });

  startExperimentButton.addEventListener("click", function() {
    fetch("/start-experiment", {method: "POST"})
      .then(response => response.text())
      .then(data => console.log(data));
  });

  shutdownButton.addEventListener("click", function() {
      fetch("/shutdown", {method: "POST"})
        .then(response => response.text())
        .then(data => console.log(data));
  });

  startMitigationButton.addEventListener("click", function() {
      fetch("/start-mitigation", {method: "POST"})
        .then(response => response.text())
        .then(data => console.log(data));
  });
  
  stopMitigationButton.addEventListener("click", function() {
      fetch("/stop-mitigation", {method: "POST"})
        .then(response => response.text())
        .then(data => console.log(data));
  });
  
});