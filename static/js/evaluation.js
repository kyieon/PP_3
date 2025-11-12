function displayEvaluationResults(spanCount) {
    const container = document.getElementById("evaluationResults");
    if (!container) {
        console.log('상태평가 결과 컨테이너가 없습니다. 건너뜑니다.');
        return;
    }
    container.innerHTML = "";

    const headers = [
        "바닥판", "거더", "가로보", "포장", "배수", "난간연석", "신축이음",
        "교량받침", "하부", "기초", "탄산화_상부", "탄산화_하부"
    ];

    const table = document.createElement("table");
    table.className = "table table-bordered text-center evaluation-table";

    const thead = document.createElement("thead");
    const headerRow1 = document.createElement("tr");
    headerRow1.innerHTML = '<th rowspan="2">번호</th><th rowspan="2">구조형식</th>' +
        '<th colspan="2">상부구조</th>' +
        '<th>2차부재</th>' +
        '<th colspan="4">기타부재</th>' +
        '<th>받침</th>' +
        '<th colspan="2">하부구조</th>' +
        '<th colspan="2">내구성요소</th>';

    const headerRow2 = document.createElement("tr");
    headers.forEach(h => {
        const th = document.createElement("th");
        th.innerText = h;
        headerRow2.appendChild(th);
    });

    thead.appendChild(headerRow1);
    thead.appendChild(headerRow2);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");

    const makeRow = (label, structure) => {
        const row = document.createElement("tr");
        row.innerHTML = `<td>${label}</td><td>${structure}</td>` +
            headers.map(() => `<td>b</td>`).join("");
        return row;
    };

    tbody.appendChild(makeRow("A1(S1)", "PSCI"));
    for (let i = 1; i < spanCount; i++) {
        tbody.appendChild(makeRow(`P${i}(S${i + 1})`, "PSCI"));
    }
    tbody.appendChild(makeRow("A2", "-"));

    const bottomLabels = [
        { label: "평균", value: "0.200" },
        { label: "가중치", value: "10" },
        { label: "(평균×가중치)/합", value: "0.015" }
    ];
    bottomLabels.forEach(entry => {
        const row = document.createElement("tr");
        row.innerHTML = `<td colspan="2"><strong>${entry.label}</strong></td>` +
            headers.map(() => `<td>${entry.value}</td>`).join("");
        tbody.appendChild(row);
    });

    const rowDefect = document.createElement("tr");
    rowDefect.innerHTML = `<td colspan="${headers.length + 1}">환산 결함도 점수</td><td>0.223</td>`;
    tbody.appendChild(rowDefect);

    const rowGrade = document.createElement("tr");
    rowGrade.innerHTML = `<td colspan="${headers.length + 1}">상태평가 결과</td><td>B</td>`;
    tbody.appendChild(rowGrade);

    table.appendChild(tbody);
    if (container) {
        container.appendChild(table);
    }
}

// 교량명 드롭다운 관련 기능
function loadBridgeList() {
    console.log('교량 목록 로딩 시작');
    
    fetch('/api/bridge_list')
        .then(response => response.json())
        .then(data => {
            console.log('교량 목록 응답:', data);
            
            if (data.success) {
                const bridgeSelect = document.getElementById('bridgeName');
                
                // 기존 옵션 제거 (첫 번째 기본 옵션 제외)
                while (bridgeSelect.children.length > 1) {
                    bridgeSelect.removeChild(bridgeSelect.lastChild);
                }
                
                // 교량 목록 추가
                data.bridges.forEach(bridge => {
                    const option = document.createElement('option');
                    option.value = bridge.filename;
                    option.textContent = `${bridge.bridge_name} (${bridge.upload_date})`;
                    option.dataset.bridgeName = bridge.bridge_name;
                    bridgeSelect.appendChild(option);
                });
                
                console.log(`총 ${data.bridges.length}개 교량 로딩 완료`);
            } else {
                console.error('교량 목록 로딩 실패:', data.error);
            }
        })
        .catch(error => {
            console.error('교량 목록 로딩 중 오류:', error);
        });
}

function loadBridgeData(filename) {
    console.log('교량 데이터 로딩 시작:', filename);
    
    if (!filename) {
        console.log('파일명이 없어 폼 초기화');
        resetForm();
        return;
    }
    
    fetch(`/api/bridge_data/${filename}`)
        .then(response => response.json())
        .then(data => {
            console.log('교량 데이터 응답:', data);
            
            if (data.success) {
                const bridgeData = data.data;
                
                // 폼 필드에 데이터 채우기
                if (bridgeData.structure_type) {
                    const structureSelect = document.getElementById('structureType');
                    // 구조형식 매핑
                    const structureMap = {
                        'PSC 박스거더교': 'psc',
                        'PSC 빔교': 'psc', 
                        'PSC': 'psc',
                        '강박스거더교': 'steel',
                        '강플레이트거더교': 'steel',
                        '강': 'steel',
                        'RC 슬래브교': 'rc',
                        'RC': 'rc',
                        '라멘교': 'rc',
                        '합성': 'composite'
                    };
                    
                    const mappedType = structureMap[bridgeData.structure_type] || bridgeData.structure_type.toLowerCase();
                    structureSelect.value = mappedType;
                    console.log('구조형식 설정:', bridgeData.structure_type, '->', mappedType);
                } else {
                    console.log('구조형식 데이터 없음');
                }
                
                if (bridgeData.length > 0) {
                    document.getElementById('length').value = bridgeData.length;
                    console.log('길이 설정:', bridgeData.length);
                }
                
                if (bridgeData.width > 0) {
                    document.getElementById('width').value = bridgeData.width;
                    console.log('폭 설정:', bridgeData.width);
                }
                
                if (bridgeData.span_count > 0) {
                    document.getElementById('spanCount').value = bridgeData.span_count;
                    console.log('경간수 설정:', bridgeData.span_count);
                    // 경간수가 변경되면 상태평가 테이블도 업데이트
                    displayEvaluationResults(bridgeData.span_count);
                }
                
                // 신축이음 위치 처리
                if (data.expansion_joint_location || data.expansionJointLocations) {
                    bridgeData.expansionJointLocations = data.expansion_joint_location || data.expansionJointLocations;
                    console.log('신축이음 위치 로딩:', bridgeData.expansionJointLocations);
                    loadExpansionJoints(bridgeData.expansionJointLocations);
                } else {
                    bridgeData.expansionJointLocations = '';
                    console.log('신축이음 위치가 없습니다.');
                }
                
                console.log('교량 데이터 로딩 완료');
            } else {
                console.error('교량 데이터 로딩 실패:', data.error);
                alert('교량 데이터를 불러오는데 실패했습니다: ' + data.error);
            }
        })
        .catch(error => {
            console.error('교량 데이터 로딩 중 오류:', error);
            alert('교량 데이터를 불러오는 중 오류가 발생했습니다.');
        });
}

function resetForm() {
    console.log('폼 초기화');
    
    // 모든 입력 필드 초기화
    document.getElementById('structureType').value = 'rc';
    document.getElementById('length').value = '';
    document.getElementById('width').value = '';
    document.getElementById('spanCount').value = '';
    
    // 부재별 면적 초기화
    document.getElementById('girderArea').value = '';
    document.getElementById('deckArea').value = '';
    document.getElementById('abutmentArea').value = '';
    document.getElementById('pierArea').value = '';
    
    // 신축이음 초기화
    resetExpansionJoints();
    
    // 부재별 상태평가 초기화
    const evaluationFields = [
        'girderCrackWidth', 'girderSurfaceDamage', 'girderRebarCorrosion', 'girderConcreteStrength',
        'deckCrackWidth', 'deckSurfaceDamage',
        'abutmentCrackWidth', 'abutmentSurfaceDamage',
        'pierCrackWidth', 'pierSurfaceDamage'
    ];
    
    evaluationFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) field.value = '';
    });
}

function loadExpansionJoints(jointData) {
    console.log('신축이음 데이터 로딩:', jointData);
    
    try {
        // 신축이음 데이터 처리
        let joints = [];
        
        if (typeof jointData === 'string' && jointData.trim()) {
            // 문자열인 경우 그대로 사용 (위치 정보가 숫자가 아니더라도)
            const splitData = jointData.split(/[,\s]+/).map(j => j.trim()).filter(j => j.length > 0);
            console.log('분리된 데이터:', splitData);
            
            // 숫자로 변환 가능한 것은 숫자로, 나머지는 그대로 사용
            joints = splitData.map(j => {
                const num = parseFloat(j);
                return !isNaN(num) ? num : j;
            });
        } else if (Array.isArray(jointData)) {
            joints = jointData;
        } else if (typeof jointData === 'number') {
            joints = [jointData];
        }
        
        console.log('처리된 신축이음 위치:', joints);
        
        if (joints.length > 0) {
            // 기존 신축이음 초기화
            resetExpansionJoints();
            
            // 첫 번째 신축이음은 이미 존재하므로 값만 설정
            const firstInput = document.querySelector('input[name="expansionJoint"]');
            if (firstInput && joints[0] !== undefined) {
                firstInput.value = joints[0];
                console.log('첫 번째 신축이음 설정:', joints[0]);
            }
            
            // 나머지 신축이음 추가
            for (let i = 1; i < joints.length; i++) {
                addExpansionJoint();
                // 새로 추가된 입력 요소에 값 설정
                setTimeout(() => {
                    const inputs = document.querySelectorAll('input[name="expansionJoint"]');
                    if (inputs[i]) {
                        inputs[i].value = joints[i];
                        console.log(`${i+1}번째 신축이음 설정:`, joints[i]);
                    }
                }, 10);
            }
        }
    } catch (error) {
        console.error('신축이음 데이터 처리 중 오류:', error);
    }
}

function resetExpansionJoints() {
    console.log('신축이음 초기화');
    
    const container = document.getElementById('expansionJoints');
    if (container) {
        // 첫 번째 신축이음만 남기고 모두 제거
        while (container.children.length > 1) {
            container.removeChild(container.lastChild);
        }
        
        // 첫 번째 신축이음 값 초기화
        const firstInput = container.querySelector('input[name="expansionJoint"]');
        if (firstInput) {
            firstInput.value = '';
        }
    }
}

// 페이지 로딩 시 초기화
document.addEventListener("DOMContentLoaded", () => {
    console.log('페이지 로딩 완료, 초기화 시작');
    
    // 교량 목록 로딩
    loadBridgeList();
    
    // 교량명 선택 이벤트 리스너
    const bridgeSelect = document.getElementById('bridgeName');
    if (bridgeSelect) {
        bridgeSelect.addEventListener('change', function() {
            console.log('교량 선택 변경:', this.value);
            loadBridgeData(this.value);
        });
    }
    
    // 경간수 입력 이벤트 리스너
    const spanInput = document.getElementById("spanCount");
    if (spanInput) {
        spanInput.addEventListener("input", () => {
            const value = parseInt(spanInput.value);
            if (!isNaN(value) && value > 0) {
                console.log('경간수 변경:', value);
                displayEvaluationResults(value);
            }
        });
    }
    
    // 초기 테이블 표시 (기본 3경간)
    displayEvaluationResults(3);
});

// 신축이음 추가 기능
function addExpansionJoint() {
    console.log('신축이음 추가');
    
    const container = document.getElementById('expansionJoints');
    const newRow = document.createElement('div');
    newRow.className = 'row mb-3';
    
    newRow.innerHTML = `
        <div class="col-md-10">
            <label class="form-label">신축이음 위치</label>
            <input type="text" class="form-control" name="expansionJoint" required>
        </div>
        <div class="col-md-2 d-flex align-items-end">
            <button type="button" class="btn btn-danger" onclick="removeExpansionJoint(this)">삭제</button>
        </div>
    `;
    
    container.appendChild(newRow);
}

// 신축이음 삭제 기능
function removeExpansionJoint(button) {
    console.log('신축이음 삭제');
    
    const row = button.closest('.row');
    if (row) {
        row.remove();
    }
}

// 폼 제출 처리
function handleFormSubmit(event) {
    event.preventDefault();
    console.log('폼 제출 시작');
    
    // 폼 데이터 수집
    const formData = new FormData(event.target);
    const data = {};
    
    // 기본 데이터 수집
    for (let [key, value] of formData.entries()) {
        if (key === 'expansionJoint') {
            if (!data.expansionJoints) data.expansionJoints = [];
            data.expansionJoints.push(parseFloat(value));
        } else {
            data[key] = value;
        }
    }
    
    console.log('수집된 데이터:', data);
    
    // 여기에 상태평가 로직 추가 가능
    // 예: 서버로 데이터 전송 및 결과 처리
    
    // 결과 표시 영역 나타내기
    const resultDiv = document.getElementById('result');
    if (resultDiv) {
        resultDiv.style.display = 'block';
        document.getElementById('resultContent').innerHTML = `
            <div class="alert alert-success">
                <h4>평가 완료</h4>
                <p>교량명: ${data.bridgeName}</p>
                <p>구조형식: ${data.structureType}</p>
                <p>경간수: ${data.spanCount}</p>
            </div>
        `;
    }
}
