// 보수물량표의 입력 필드 변경 감지
document.addEventListener('DOMContentLoaded', function () {
    const repairTable = document.querySelector('.repair-table');
    if (!repairTable) return;

    // 모든 변경 이벤트를 하나의 리스너로 통합
    repairTable.addEventListener('change', function (e) {
        if (e.target.classList.contains('repair-method') ||
            e.target.classList.contains('priority') ||
            e.target.classList.contains('unit-price')) {
            updateRepairData();
        }
    });
});

// 보수물량표 데이터 수집 및 서버 전송
function updateRepairData() {
    const rows = document.querySelectorAll('.repair-table tbody tr');
    const repairData = [];

    rows.forEach(row => {
        const cells = row.cells;
        const repairMethod = row.querySelector('.repair-method').value;
        const priority = row.querySelector('.priority').value;
        const unitPrice = parseInt(row.querySelector('.unit-price').value.replace(/,/g, ''));
        const quantity = parseFloat(cells[3].textContent);
        const count = parseInt(cells[4].textContent);

        repairData.push({
            component: cells[0].textContent,
            damage: cells[1].textContent,
            repairMethod: repairMethod,
            priority: priority,
            unitPrice: unitPrice,
            quantity: quantity,
            count: count
        });
    });

    // 서버에 데이터 전송
    fetch('/update_repair', {
        method: 'POST', 
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(repairData)
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error:', data.error);
                return;
            }
            if (data.cost_table) {
                document.querySelector('.cost-table').innerHTML = data.cost_table;
            }
            if (data.priority_table) {
                document.querySelector('.priority-table').innerHTML = data.priority_table;
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// 상태평가 관련 JavaScript 코드
document.addEventListener('DOMContentLoaded', function () {
    const evaluateButton = document.getElementById('evaluateButton');
    const saveEvaluation = document.getElementById('saveEvaluation');
    const evaluationResult = document.getElementById('evaluationResult');
    const structureType = document.getElementById('structureType');

    if (evaluateButton) {
        evaluateButton.addEventListener('click', function () {
            const formData = {
                bridgeName: document.getElementById('bridgeName').value,
                length: parseFloat(document.getElementById('length').value),
                width: parseFloat(document.getElementById('width').value),
                structureType: document.getElementById('structureType').value,
                spanCount: parseInt(document.getElementById('spanCount').value),
                defects: [] // 부재별 손상 데이터는 나중에 추가
            };

            // 서버에 평가 요청
            fetch('/evaluate_bridge', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        evaluationResult.innerHTML = data.evaluation_html;
                    } else {
                        evaluationResult.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    }
                })
                .catch(error => {
                    evaluationResult.innerHTML = `<div class="alert alert-danger">평가 중 오류가 발생했습니다: ${error}</div>`;
                });
        });
    }

    if (saveEvaluation) {
        saveEvaluation.addEventListener('click', function () {
            // 평가 결과 저장 로직 구현
            alert('평가 결과가 저장되었습니다.');
        });
    }

    if (structureType) {
        structureType.addEventListener('change', function () {
            updateComponentEvaluation(this.value);
        });
    }
});

function updateComponentEvaluation(structureType) {
    const componentEvaluation = document.getElementById('componentEvaluation');
    if (!componentEvaluation) return;

    // 구조형식에 따른 평가 항목 설정
    const components = getComponentsByStructureType(structureType);

    let html = '';
    components.forEach(component => {
        html += `
            <div class="component-group">
                <h5>${component.name}</h5>
                <div class="form-group">
                    <label>손상도</label>
                    <input type="range" class="form-range" min="0" max="100" value="0" 
                           id="${component.id}_damage" name="${component.id}_damage">
                </div>
                <div class="form-group">
                    <label>중요도</label>
                    <select class="form-select" id="${component.id}_importance" name="${component.id}_importance">
                        <option value="1">낮음</option>
                        <option value="2">보통</option>
                        <option value="3">높음</option>
                    </select>
                </div>
            </div>
        `;
    });

    componentEvaluation.innerHTML = html;
}

function getComponentsByStructureType(type) {
    // 구조형식별 평가 대상 부재 목록
    const componentsByType = {
        'PSCI': [
            { id: 'girder', name: '거더' },
            { id: 'slab', name: '슬래브' },
            { id: 'crossbeam', name: '가로보' },
            { id: 'bearing', name: '받침' },
            { id: 'expansion_joint', name: '신축이음' },
        ],
        'STB': [
            { id: 'main_girder', name: '주거더' },
            { id: 'slab', name: '슬래브' },
            { id: 'crossbeam', name: '가로보' },
            { id: 'connection', name: '연결부' },
            { id: 'bearing', name: '받침' },
        ],
        'RCS': [
            { id: 'slab', name: '슬래브' },
            { id: 'abutment', name: '교대' },
            { id: 'pier', name: '교각' },
            { id: 'foundation', name: '기초' },
        ],
        'RA': [
            { id: 'arch_rib', name: '아치리브' },
            { id: 'spandrel', name: '스팬드럴' },
            { id: 'deck', name: '바닥판' },
            { id: 'pier', name: '교각' },
        ],
        'PSC BOX': [
            { id: 'box_girder', name: '박스거더' },
            { id: 'diaphragm', name: '다이아프램' },
            { id: 'bearing', name: '받침' },
            { id: 'pier', name: '교각' },
        ]
    };

    return componentsByType[type] || [];
} 