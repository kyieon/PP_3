// 면적 계산 함수
function calculateAreas() {
    const length = parseFloat(document.getElementById('length').value);
    const width = parseFloat(document.getElementById('width').value);
    const spanCount = parseInt(document.getElementById('spanCount').value);

    if (isNaN(length) || isNaN(width) || isNaN(spanCount)) {
        alert('연장, 폭, 경간 수를 모두 입력해주세요.');
        return;
    }

    // 바닥판 면적 = 연장 × 폭
    const slabArea = length * width;
    document.getElementById('slabArea').value = slabArea.toFixed(2);

    // 교면포장 면적 = 연장 × 폭
    document.getElementById('pavementArea').value = slabArea.toFixed(2);

    // 연석 면적 = 연장 × 2 (좌우)
    const curbArea = length * 2;
    document.getElementById('curbArea').value = curbArea.toFixed(2);
}

// 상태평가 함수
function evaluateBridge() {
    const formData = {
        bridgeName: document.getElementById('bridgeName').value,
        length: parseFloat(document.getElementById('length').value),
        width: parseFloat(document.getElementById('width').value),
        structureType: document.getElementById('structureType').value,
        spanCount: parseInt(document.getElementById('spanCount').value),
        expansionJoint: document.getElementById('expansionJoint').value,
        
        // 부재별 타입 정보
        slabType: document.getElementById('slabType').value,
        girderType: document.getElementById('girderType').value,
        crossbeamType: document.getElementById('crossbeamType').value,
        pavementType: document.getElementById('pavementType').value
    };

    // 필수 입력값 검증
    for (const [key, value] of Object.entries(formData)) {
        if (value === undefined || value === null || value === '') {
            alert(`${key}을(를) 입력해주세요.`);
            return;
        }
    }

    // 서버에 평가 요청
    fetch('/evaluate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
        .then(response => response.json())
        .then(data => {
            // 평가 결과 표시
            displayEvaluationResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('상태평가 중 오류가 발생했습니다.');
        });
}

// 평가 결과 표시 함수
function displayEvaluationResults(data) {
    const tbody = document.getElementById('evaluationResults');
    tbody.innerHTML = '';

    let totalWeight = 0;
    let totalDefectScore = 0;
    let componentCount = 0;

    data.evaluation_results.forEach(result => {
        result.span_evaluations.forEach(evaluation => {
            const row = document.createElement('tr');

            // 상태등급에 따른 클래스 설정
            const gradeClass = `grade-${evaluation.grade.toLowerCase()}`;

            row.innerHTML = `
                <td>${result.component}</td>
                <td>${evaluation.span}</td>
                <td>${evaluation.area.toFixed(2)}</td>
                <td>${(evaluation.area_ratio * 100).toFixed(2)}</td>
                <td>${evaluation.weight.toFixed(2)}</td>
                <td class="${gradeClass}">${evaluation.grade.toUpperCase()}</td>
                <td>${evaluation.defect_score.toFixed(2)}</td>
            `;

            tbody.appendChild(row);

            totalWeight += evaluation.weight;
            totalDefectScore += evaluation.defect_score;
            componentCount++;
        });
    });

    // 평균 계산
    const avgWeight = totalWeight / componentCount;
    const avgDefectScore = totalDefectScore / componentCount;

    // 최종 등급 계산
    let finalGrade = 'A';
    if (avgDefectScore >= 0.79) finalGrade = 'E';
    else if (avgDefectScore >= 0.49) finalGrade = 'D';
    else if (avgDefectScore >= 0.26) finalGrade = 'C';
    else if (avgDefectScore >= 0.13) finalGrade = 'B';

    // 결과 업데이트
    document.getElementById('avgWeight').textContent = avgWeight.toFixed(2);
    document.getElementById('avgDefectScore').textContent = avgDefectScore.toFixed(2);
    document.getElementById('sumWeight').textContent = totalWeight.toFixed(2);
    document.getElementById('sumDefectScore').textContent = totalDefectScore.toFixed(2);
    document.getElementById('finalGrade').textContent = finalGrade;
    document.getElementById('finalGrade').className = `grade-${finalGrade.toLowerCase()}`;

    // 콘크리트 바닥판 평가 결과 표시
    const concreteSlabResults = document.getElementById('concreteSlabResults');
    if (concreteSlabResults && data.concrete_slab_evaluation) {
        concreteSlabResults.innerHTML = '';
        
        data.concrete_slab_evaluation.forEach(result => {
            const row = document.createElement('tr');
            
            // 등급에 따른 클래스 설정
            const gradeClass = `grade-${result.grade.toLowerCase()}`;
            
            row.innerHTML = `
                <td>${result.section}</td>
                <td>${result.inspection_area.toFixed(1)}</td>
                <td>${result.crack_1_width || '-'}</td>
                <td class="${gradeClass}">${result.crack_1_ratio || 'a'}</td>
                <td>${result.crack_2_width || '-'}</td>
                <td class="${gradeClass}">${result.crack_2_ratio || 'a'}</td>
                <td>${result.leakage_ratio?.toFixed(2) || '-'}</td>
                <td>${result.surface_damage_ratio?.toFixed(3) || '-'}</td>
                <td>${result.rebar_corrosion_ratio?.toFixed(2) || '-'}</td>
                <td class="${gradeClass}">${result.evaluation_grade}</td>
            `;
            
            concreteSlabResults.appendChild(row);
        });
    }
}

// 할증율 저장 함수
function saveMarkupRate(filename) {
    const markupRate = document.getElementById('markup_rate').value;
    
    if (!markupRate || isNaN(markupRate)) {
        alert('유효한 할증율을 입력해주세요.');
        return;
    }
    
    const rate = parseFloat(markupRate);
    if (rate < 0 || rate > 100) {
        alert('할증율은 0~100% 범위여야 합니다.');
        return;
    }
    
    // 서버에 할증율 저장 요청
    fetch('/api/save_markup_rate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            filename: filename,
            markup_rate: rate
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            // 페이지 새로고침하여 업데이트된 할증율 반영
            location.reload();
        } else {
            alert('할증율 저장 실패: ' + data.error);
        }
    })
    .catch(error => {
        console.error('할증율 저장 중 오류:', error);
        alert('할증율 저장 중 오류가 발생했습니다.');
    });
}

// 이벤트 리스너 등록
document.addEventListener('DOMContentLoaded', function () {
    // document.getElementById('calculateAreas').addEventListener('click', calculateAreas);
    document.getElementById('evaluateBridge').addEventListener('click', evaluateBridge);
}); 