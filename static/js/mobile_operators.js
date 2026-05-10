let operatorModal;

document.addEventListener("DOMContentLoaded", () => {
    loadOperators();
    // Initialize Bootstrap modal
    operatorModal = new bootstrap.Modal(document.getElementById('operatorModal'));
});

async function loadOperators() {
    try {
        const response = await fetch("/recharge/operators", {
            headers: Auth.getAuthHeader()
        });
        const result = await response.json();
        
        if (result.success) {
            const tbody = document.getElementById("operatorsTableBody");
            tbody.innerHTML = "";
            
            result.data.operators.forEach(op => {
                tbody.innerHTML += `
                    <tr>
                        <td><img src="${op.logo_url}" width="40" height="40" class="rounded-circle"></td>
                        <td>${op.operator_name}</td>
                        <td>${op.country_code}</td>
                        <td><span class="badge ${op.status === 'active' ? 'badge-success' : 'badge-warning'}">${op.status}</span></td>
                        <td>
                            <button class="btn btn-sm btn-info" onclick="editOperator('${op.operator_id}')">Edit</button>
                            <button class="btn btn-sm btn-danger" onclick="toggleOperatorStatus('${op.operator_id}', '${op.status}')">
                                ${op.status === 'active' ? 'Disable' : 'Enable'}
                            </button>
                        </td>
                    </tr>
                `;
            });
        }
    } catch (error) {
        console.error("Failed to load operators", error);
    }
}

function showAddOperatorModal() {
    document.getElementById("operatorModalTitle").innerText = "Add New Operator";
    document.getElementById("operatorForm").reset();
    document.getElementById("operatorId").value = "";
    operatorModal.show();
}

async function editOperator(operatorId) {
    try {
        const response = await fetch("/recharge/operators", {
            headers: Auth.getAuthHeader()
        });
        const result = await response.json();
        const operator = result.data.operators.find(op => op.operator_id === operatorId);

        if (operator) {
            document.getElementById("operatorModalTitle").innerText = "Edit Operator";
            document.getElementById("operatorId").value = operator.operator_id;
            document.getElementById("opName").value = operator.operator_name;
            document.getElementById("opCountry").value = operator.country_code;
            document.getElementById("opLogo").value = operator.logo_url;
            document.getElementById("opApi").value = operator.operator_api || "";
            operatorModal.show();
        }
    } catch (error) {
        console.error("Error loading operator details:", error);
        showToast("Failed to load operator details", "error");
    }
}

async function saveOperator() {
    const opId = document.getElementById("operatorId").value;
    const payload = {
        user_id: localStorage.getItem('admin_id') || "USRDCAFAC40FA144DE5ABAD95E9D79D066C",
        access_token: localStorage.getItem('admin_access_token') || "",
        android_id: "web_admin_panel",
        android_uuid: "web_admin_uuid",
        user_password: document.getElementById("adminPassword").value,
        operator_name: document.getElementById("opName").value,
        country_code: document.getElementById("opCountry").value,
        logo_url: document.getElementById("opLogo").value,
        operator_api: document.getElementById("opApi").value
    };

    if (!payload.user_password) {
        return showToast("Admin password is required", "error");
    }

    // যদি opId থাকে তাহলে আপডেট API কল হবে, না থাকলে নতুন অ্যাড হবে
    const endpoint = opId ? "/recharge/operator-update" : "/recharge/new-operator";
    const method = opId ? "PUT" : "POST";
    if (opId) payload.operator_id = opId;

    try {
        const response = await fetch(endpoint, {
            method: method,
            headers: { "Content-Type": "application/json", ...Auth.getAuthHeader() },
            body: JSON.stringify(payload)
        });

        const result = await response.json();
        if (result.success) {
            showToast(opId ? "Operator updated!" : "Operator added!", "success");
            operatorModal.hide();
            loadOperators();
        } else {
            showToast(result.message || "Operation failed", "error");
        }
    } catch (error) {
        showToast("Server error", "error");
    }
}

async function toggleOperatorStatus(operatorId, currentStatus) {
    // নোট: আপনার বর্তমানে শুধুমাত্র /recharge/deactivate-operator আছে। 
    // আপনাকে /recharge/activate-operator API-টি তৈরি করে নিতে হবে।
    const endpoint = currentStatus === 'active' ? "/recharge/deactivate-operator" : "/recharge/activate-operator";

    try {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...Auth.getAuthHeader()
            },
            body: JSON.stringify({ operator_id: operatorId })
        });

        if (response.status === 404) {
            return showToast('API endpoint not found. Please create the activation API.', 'error');
        }

        const result = await response.json();
        if (result.success) {
            showToast(result.message, 'success');
            loadOperators(); // টেবিল রিফ্রেশ করবে
        } else {
            showToast(result.message || 'Operation failed', 'error');
        }
    } catch (error) {
        console.error("Error toggling status:", error);
        showToast('Error connecting to server', 'error');
    }
}