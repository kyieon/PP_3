var get_span_damage = [];

let bridgeData = {
    id: '',
    name: '',
    structureType: '',
    length: 0,
    width: 0,
    spanCount: 0,
    expansionJointLocations: '',
    spans: []

};
var showResponseData;
var damageDataStr = '';

function calculateCurbArea($cell,newRatio,crackData2d) {

     let cellHtml = $cell.html();
     //alert(newRatio);
    if(newRatio > 0 ){

        if (cellHtml.includes('<br>')) {
          let [first, ] = cellHtml.split('<br>');
          $cell.html(first + '<br>' + newRatio.safeToFixed(2)).attr('data-original-value', crackData2d);

        } else {
           $cell.text(newRatio.safeToFixed(2)).attr('data-original-value', crackData2d);
         }

    } else {
      $cell.html('-').attr('data-original-value', crackData2d);


    }






}
// 탄산화 등급 변경 시 통합산정결과표 재계산 함수 (전역 스코프)
function recalculateTotalEvaluationTable() {
    console.log('통합산정결과표 재계산 시작');

    const tableElement = document.getElementById('totalEvaluationTable');
    if (!tableElement) {
        console.log('통합산정결과표를 찾을 수 없음');
        return;
    }

    // 탄산화 등급 수집 및 평균 계산
    const carbonationScores = {
        upper: [],
        lower: []
    };

    // 모든 탄산화 드롭다운에서 선택된 값 수집
    $('.carbonation-grade').each(function() {
        const selectedValue = $(this).val();
        const type = $(this).data('type');

        console.log(`드롭다운 값: ${selectedValue}, 타입: ${type}`);

        if (selectedValue && selectedValue !== '') {
            const score = gradeToDefectScore(selectedValue);
            console.log(`등급 ${selectedValue} -> 점수 ${score}`);

            if (type === 'upper') {
                carbonationScores.upper.push(score);
            } else if (type === 'lower') {
                carbonationScores.lower.push(score);
            }
        }
    });

    console.log('탄산화 점수 수집 결과:', carbonationScores);

    // 탄산화 상부/하부 평균 계산
    const carbonationAverages = {
        upper: carbonationScores.upper.length > 0 ?
            carbonationScores.upper.reduce((sum, score) => sum + score, 0) / carbonationScores.upper.length : 0.0,
        lower: carbonationScores.lower.length > 0 ?
            carbonationScores.lower.reduce((sum, score) => sum + score, 0) / carbonationScores.lower.length : 0.0
    };

    console.log('탄산화 평균:', carbonationAverages);

    // 평균 행 업데이트 - 정확한 행 찾기
    const allRows = tableElement.querySelectorAll('tr');
    let averageRow = null;

    for (let row of allRows) {
        const firstCell = row.querySelector('td[colspan="2"]');
        if (firstCell && firstCell.textContent.trim() === '평균') {
            averageRow = row;
            break;
        }
    }

    if (averageRow) {
        const cells = averageRow.getElementsByTagName('td');
        console.log(`평균 행 셀 개수: ${cells.length}`);

        // colspan="2" 때문에 인덱스 조정 필요
        // 첫 번째 셀이 colspan="2"이므로 실제 데이터 셀은 1번째부터 시작
        if (cells.length >= 14) {
            // 탄산화 상부 (11번째 인덱스)
            cells[11].textContent = carbonationAverages.upper.safeToFixed(3);
            // 탄산화 하부 (12번째 인덱스)
            cells[12].textContent = carbonationAverages.lower.safeToFixed(3);

            console.log(`평균 행 업데이트: 상부=${carbonationAverages.upper.safeToFixed(3)}, 하부=${carbonationAverages.lower.safeToFixed(3)}`);
        }
    } else {
        console.log('평균 행을 찾을 수 없음');
    }

    // 가중치 가져오기
    const weights = {
        slab: Number($('#weightSlab').val()) || 0,
        girder: Number($('#weightGirder').val()) || 0,
        crossbeam: Number($('#weightCrossbeam').val()) || 0,
        pavement: Number($('#weightPavement').val()) || 0,
        drainage: Number($('#weightDrainage').val()) || 0,
        railing: Number($('#weightRailing').val()) || 0,
        expansionJoint: Number($('#weightExpansionJoint').val()) || 0,
        bearing: Number($('#weightBearing').val()) || 0,
        abutment: Number($('#weightAbutment').val()) || 0,
        foundation: Number($('#weightFoundation').val()) || 0,
        carbonation_upper: Number($('#weightCarbonationUpper').val()) || 0,
        carbonation_lower: Number($('#weightCarbonationLower').val()) || 0
    };

    const totalWeight = Object.values(weights).reduce((sum, weight) => sum + weight, 0);
    console.log('가중치:', weights, '총 가중치:', totalWeight);

    // 가중평균 행 업데이트 - 정확한 행 찾기
    let weightedRow = null;
    for (let row of allRows) {
        const firstCell = row.querySelector('td[colspan="2"]');
        if (firstCell && (firstCell.textContent.includes('가중치') && firstCell.textContent.includes('평균'))) {
            weightedRow = row;
            break;
        }
    }

    if (weightedRow && totalWeight > 0) {
        const cells = weightedRow.getElementsByTagName('td');
        console.log(`가중평균 행 셀 개수: ${cells.length}`);

        if (cells.length >= 14) {
            // 탄산화 상부 가중평균
            const upperWeighted = ((carbonationAverages.upper * weights.carbonation_upper) / totalWeight).safeToFixed(3);
            cells[11].textContent = upperWeighted;

            // 탄산화 하부 가중평균
            const lowerWeighted = ((carbonationAverages.lower * weights.carbonation_lower) / totalWeight).safeToFixed(3);
            cells[12].textContent = lowerWeighted;

            console.log(`가중평균 행 업데이트: 상부=${upperWeighted}, 하부=${lowerWeighted}`);
        }
    } else {
        console.log('가중평균 행을 찾을 수 없거나 총 가중치가 0임');
    }

    // 최종 점수 및 등급 재계산 (다른 부재들의 평균도 포함)
    if (typeof updateFinalScoreAndGrade === 'function') {
        updateFinalScoreAndGrade();
    }

    // 점수 테이블도 함께 업데이트
    updateScoreEvaluationTable(carbonationAverages);

    console.log('통합산정결과표 재계산 완료');
}

// 점수 테이블 업데이트 함수
function updateScoreEvaluationTable(carbonationAverages) {
    console.log('점수 테이블 업데이트 시작');

    const scoreTableElement = document.getElementById('totalScoreEvaluationTable');
    if (!scoreTableElement) {
        console.log('점수 테이블을 찾을 수 없음');
        return;
    }

    // 등급을 점수로 변환하는 함수
    const gradeToScore = (grade) => {
        const gradeMap = { 'a': 0.1, 'b': 0.2, 'c': 0.4, 'd': 0.7, 'e': 1.0 };
        return gradeMap[grade.toLowerCase()] || null;
    };

    // 점수 테이블의 모든 행을 업데이트
    const allRows = scoreTableElement.querySelectorAll('tbody tr');

    // 평균 행 찾기 및 업데이트
    let averageRow = null;
    for (let row of allRows) {
        const firstCell = row.querySelector('td[colspan="2"]');
        if (firstCell && firstCell.textContent.trim() === '평균') {
            averageRow = row;
            break;
        }
    }

    if (averageRow) {
        const cells = averageRow.getElementsByTagName('td');
        if (cells.length >= 14) {
            // 탄산화 상부/하부 점수 업데이트
            cells[11].textContent = carbonationAverages.upper.safeToFixed(3);
            cells[12].textContent = carbonationAverages.lower.safeToFixed(3);
            console.log(`점수 테이블 평균 행 업데이트: 상부=${carbonationAverages.upper.safeToFixed(3)}, 하부=${carbonationAverages.lower.safeToFixed(3)}`);
        }
    }

    // 가중평균 행 업데이트
    const weights = {
        carbonation_upper: Number($('#weightCarbonationUpper').val()) || 0,
        carbonation_lower: Number($('#weightCarbonationLower').val()) || 0
    };

    const totalWeight = Number($('#weightSlab').val() || 0) + Number($('#weightGirder').val() || 0) +
                       Number($('#weightCrossbeam').val() || 0) + Number($('#weightPavement').val() || 0) +
                       Number($('#weightDrainage').val() || 0) + Number($('#weightRailing').val() || 0) +
                       Number($('#weightExpansionJoint').val() || 0) + Number($('#weightBearing').val() || 0) +
                       Number($('#weightAbutment').val() || 0) + Number($('#weightFoundation').val() || 0) +
                       weights.carbonation_upper + weights.carbonation_lower;

    let weightedRow = null;
    for (let row of allRows) {
        const firstCell = row.querySelector('td[colspan="2"]');
        if (firstCell && (firstCell.textContent.includes('가중치') && firstCell.textContent.includes('평균'))) {
            weightedRow = row;
            break;
        }
    }

    if (weightedRow && totalWeight > 0) {
        const cells = weightedRow.getElementsByTagName('td');
        if (cells.length >= 14) {
            // 탄산화 상부/하부 가중평균 점수 업데이트
            const upperWeighted = ((carbonationAverages.upper * weights.carbonation_upper) / totalWeight).safeToFixed(3);
            const lowerWeighted = ((carbonationAverages.lower * weights.carbonation_lower) / totalWeight).safeToFixed(3);

            cells[11].textContent = upperWeighted;
            cells[12].textContent = lowerWeighted;

            console.log(`점수 테이블 가중평균 행 업데이트: 상부=${upperWeighted}, 하부=${lowerWeighted}`);
        }
    }


    const totalTableElement = document.getElementById('totalEvaluationTable');
    const totalRows = totalTableElement ? totalTableElement.querySelectorAll('tbody tr') : [];

    // 개별 행들도 업데이트 (드롭다운에서 선택된 값 반영)
    allRows.forEach((row, count) => {
        const firstCell = row.cells[0];
        //if (!firstCell || firstCell.hasAttribute('colspan')) //continue;

        const position = firstCell.textContent.trim();

        const cells = row.cells;
         const degreecells = totalRows[count].getElementsByTagName('td');



        if (cells.length >= 13) {
                let selectEl = degreecells[12].querySelector("select");
                let value;

                if (selectEl) {
                    // select box가 있을 때 → 선택된 값
                    value = gradeToScore(selectEl.value);
                    // 또는 selectEl.options[selectEl.selectedIndex].text (보이는 텍스트)
                } else {
                    // select box가 없을 때 → 그냥 textContent
                    value = degreecells[12].textContent.trim();
                }
                cells[12].textContent =  value;
        }

        if (cells.length >= 14) {
            let selectEl = degreecells[13].querySelector("select");
                let value;

                if (selectEl) {
                    // select box가 있을 때 → 선택된 값
                    value = gradeToScore(selectEl.value);
                    // 또는 selectEl.options[selectEl.selectedIndex].text (보이는 텍스트)
                } else {
                    // select box가 없을 때 → 그냥 textContent
                    value = degreecells[13].textContent.trim();
                }
                cells[13].textContent =  value;
        }


        // 탄산화 드롭다운에서 선택된 값으로 점수 업데이트
        // $('.carbonation-grade').each(function() {
        //     const dropdown = $(this);
        //     const dropdownPosition = dropdown.data('position');
        //     const dropdownType = dropdown.data('type');
        //     const selectedValue = dropdown.val();

        //     if (selectedValue && position.includes(dropdownPosition)) {
        //         const score = gradeToScore(selectedValue);
        //         const cells = row.cells;

        //         if (dropdownType === 'upper' && cells.length >= 13) {
        //             cells[12].textContent = selectedValue; // 탄산화 상부 0902
        //         }
        //         if (dropdownType === 'lower' && cells.length >= 14) {
        //             cells[13].textContent = selectedValue;
        //         }
        //     }
        // });
    });

    console.log('점수 테이블 업데이트 완료');
}

// 등급을 결함도 점수로 변환하는 함수
function gradeToDefectScore(grade) {
    if (!grade || grade === '') return 0.0;

    grade = grade.toLowerCase();
    switch (grade) {
        case 'a': return 0.1;
        case 'b': return 0.2;
        case 'c': return 0.4;
        case 'd': return 0.7;
        case 'e': return 1.0;
        default: return 0.0;
    }
}

Number.prototype.safeToFixed = function(digits = 2) {
    if (isNaN(this)) return '-';
    return this.toFixed(digits);
};

String.prototype.safeToFixed = function(digits = 2) {
    if (isNaN(this)) return '-';
    const num = parseFloat(this);
    return num.toFixed(digits);
};

$(document).ready(function() {
    // 전역 변수 정의

    let damageData = {
        slab: [],
        girder: [],
        crossbeam: [],
        abutment: [],
        pier: [],
        foundation: [],
        bearing: [],
        expansionJoint: [],
        pavement: [],
        drainage: [],
        railing: []
    };

    // 저장된 교량 데이터 배열
    let savedBridges = [];

    // 디버그 로그
    console.log("교량 상태평가 스크립트 로드됨");

    // 페이지 로드 시 저장된 데이터 불러오기
    async function loadSavedBridges() {
        try {
            showLoading();
            const response = await fetch('/api/bridge_list');
            const data = await response.json();

            console.log('교량 목록 응답:', data);

            if (data.success) {
                savedBridges = [];
                data.bridges.forEach(bridge => {
                    bridge = {
                        name: bridge.bridge_name,
                        filename: bridge.filename,
                        structureType: bridge.structure_type || '-',
                        length: bridge.length || '-',
                        width: bridge.width || '-',
                        spanCount: bridge.span_count || 0,
                        expansionJointLocations: bridge.expansion_joint_location
                    };
                    savedBridges.push(bridge);
                });

                $(function () {
                    $('[data-bs-toggle="tooltip"]').tooltip();
                });

                console.log(`총 ${data.bridges.length}개 교량 로딩 완료`);
            } else {
                console.error('교량 목록 로딩 실패:', data.error);
            }

            await updateBridgeList();
            console.log('교량 목록 업데이트 완료');
            showSnackMessage('교량 목록이 성공적으로 로드되었습니다.');
                setTimeout(() => {
                     hideLoading();
                }, 2000); // 1초(1000ms) 딜레이 후 숨김



        } catch (error) {
            console.error('저장된 교량 데이터 로드 중 오류 발생:', error);
            savedBridges = [];
            hideLoading();
        }
    }

    // 초기화 함수
    function initialize() {
        // 저장된 데이터 로드
        loadSavedBridges();
        // 부재 선택 데이터 불러오기
        loadComponentSelection();
        // 교량 리스트 업데이트
        updateBridgeList();
        // 교량명 드롭다운 초기화
        initializeBridgeNameDropdown();

        // 페이지 로드 시 고정 부재명 초기화
        initializeStickyHeader();

        // /get_span_damage' 가져쥥
    }

    // 페이지 로드 시 초기화 실행
    initialize();

    // 면적 입력 이벤트 리스너 추가
    addAreaInputListeners();

    // 기초 체크박스 이벤트 리스너 추가
    $('#foundationCheck').on('change', function() {
        const isChecked = $(this).is(':checked');
        const exposedInput = $('#foundationExposedInput');

        if (isChecked) {
            exposedInput.show();
        } else {
            exposedInput.hide();
            $('#exposedFoundationPositions').val('');
        }
    });

    // 신축이음 체크박스 이벤트 리스너 추가
    $('#expansionJointCheck').on('change', function() {
        const isChecked = $(this).is(':checked');
        const locationInput = $('#expansionJointLocationInput');

        if (isChecked) {
            locationInput.show();
        } else {
            locationInput.hide();
            $('#expansionJointPositions').val('');
        }
    });

    // 페이지 로드 시 기초 체크박스 상태에 따라 노출된 기초 위치 입력 필드 표시/숨김
    if ($('#foundationCheck').is(':checked')) {
        $('#foundationExposedInput').show();
    }

    // 페이지 로드 시 신축이음 체크박스 상태에 따라 신축이음 위치 입력 필드 표시/숨김
    if ($('#expansionJointCheck').is(':checked')) {
        $('#expansionJointLocationInput').show();
    }

    // 교량명 입력 필드를 드롭다운으로 변경
    function initializeBridgeNameDropdown() {
        const bridgeNameSelect = document.getElementById('bridgeName');
        bridgeNameSelect.innerHTML = '<option value="">교량명을 선택하세요</option>';

        // 서버에서 교량 목록 가져오기
        $.ajax({
            url: '/api/bridge_list',
            method: 'GET',
            success: function(response) {
                console.log('서버 응답:', response);
                if (response.success && Array.isArray(response.bridges)) {
                    response.bridges.forEach(bridge => {
                        const option = document.createElement('option');
                        option.value = bridge.filename;  // 파일명을 value로 사용
                        option.textContent = bridge.bridge_name;  // 교량명을 표시
                        bridgeNameSelect.appendChild(option);

                });
                } else {
                    console.error('교량 목록 로드 실패:', response.error || '알 수 없는 오류');
                }
            },
            error: function(xhr, status, error) {
                console.error('교량 목록 로드 실패:', error);
            }
        });

    }

    async function loadBridgeData(filename) {
        console.log('교량 데이터 로드 시작:', filename);
        try {
            const response = await $.ajax({
                url: `/api/bridge_data/${filename}`,
                method: 'GET'
            });
            console.log('교량 데이터 로드 성공:', response);
            if (response.success) {
                const data = response.data;

                // 기본 정보 채우기
                document.getElementById('length').value = data.length || '';
                document.getElementById('width').value = data.width || '';
                document.getElementById('structureType').value = data.structure_type || '';
                document.getElementById('spanCount').value = data.span_count || '';
                document.getElementById('expansionJointLocations').value = data.expansion_joint_location || '';

                // 브리지 데이터 업데이트
                bridgeData = {
                    id: filename,
                    name: $('#bridgeName option:selected').text(),
                    structureType: data.structure_type || '',
                    length: parseFloat(data.length) || 0,
                    width: parseFloat(data.width) || 0,
                    spanCount: parseInt(data.span_count) || 0,
                    expansionJointLocations: data.expansion_joint_location || '',
                    spans: []
                };

                // 경간 데이터 생성
                if (bridgeData.spanCount > 0) {
                    generateSpansData(bridgeData.spanCount);
                }

                // 손상 데이터 처리
                if (data.has_file_data && data.damage_data) {
                    damageData = processDamageData(data.damage_data);
                    console.log('손상 데이터 처리 완료:', damageData);
                }

                // 부재 선택 카드 표시
                const componentCard = document.getElementById('componentSelectionCard');
                if (componentCard) {
                    componentCard.style.display = 'block';
                    console.log('부재 선택 카드 표시됨');
                }

                // 상태평가 생성 버튼 활성화
                const generateBtn = document.getElementById('generateEvaluation');
                if (generateBtn) {
                    generateBtn.disabled = false;
                    console.log('상태평가 생성 버튼 활성화됨');
                }

                // 저장된 가중치 불러오기
                loadEvaluationWeights();
            } else {
                console.error('교량 데이터 로드 실패:', response.error);
            }
        } catch (error) {
            console.error('교량 데이터 로드 실패:', error);
            showSnackMessage('교량 데이터를 불러오는데 실패했습니다.');
        }
    }

// 가중치 불러오기 함수
    function loadEvaluationWeights() {
        const currentFilename = window.currentSelectedFilename;
        if (!currentFilename) {
            console.log('선택된 교량이 없어 가중치를 불러오지 않습니다.');
            return;
        }

        $.ajax({
            url: '/api/load_evaluation_weights',
            method: 'GET',
            data: { filename: currentFilename },
            success: function(response) {
                if (response.success && response.weights) {
                    const weights = response.weights;
                    console.log('불러온 가중치:', weights);


                    // 가중치 입력 필드에 값 설정
                    $('#weightSlab').val(weights.slab || 0);
                    $('#weightGirder').val(weights.girder || 0);
                    $('#weightCrossbeam').val(weights.crossbeam || 0);
                    $('#weightPavement').val(weights.pavement || 0);
                    $('#weightDrainage').val(weights.drainage || 0);
                    $('#weightRailing').val(weights.railing || 0);
                    $('#weightExpansionJoint').val(weights.expansionJoint || 0);
                    $('#weightBearing').val(weights.bearing || 0);
                    $('#weightAbutment').val(weights.abutment || 0);
                    $('#weightPier').val(weights.pier || 0);
                    $('#weightFoundation').val(weights.foundation || 0);
                    $('#weightCarbonationUpper').val(weights.carbonation_upper || 0);
                    $('#weightCarbonationLower').val(weights.carbonation_lower || 0);

                    showSnackMessage('저장된 가중치를 불러왔습니다.');


                } else {
                    console.log('저장된 가중치가 없습니다.');
                    // 기본값 설정 또는 구조형식에 따른 기본 가중치 적용
                    setDefaultWeights();
                }
            },
            error: function(xhr, status, error) {
                console.error('가중치 불러오기 실패:', error);
                // 오류 시 기본값 설정
                setDefaultWeights();
            }
        });
    }


// 가중치 저장 함수
    function saveEvaluationWeights() {
        const currentFilename = window.currentSelectedFilename;
        if (!currentFilename) {
            showSnackMessage('교량을 먼저 선택해주세요.');
            return;
        }

        const weights = {
            slab: Number($('#weightSlab').val()) || 0,
            girder: Number($('#weightGirder').val()) || 0,
            crossbeam: Number($('#weightCrossbeam').val()) || 0,
            pavement: Number($('#weightPavement').val()) || 0,
            drainage: Number($('#weightDrainage').val()) || 0,
            railing: Number($('#weightRailing').val()) || 0,
            expansionJoint: Number($('#weightExpansionJoint').val()) || 0,
            bearing: Number($('#weightBearing').val()) || 0,
            abutment: Number($('#weightAbutment').val()) || 0,
            pier: Number($('#weightPier').val()) || 0,
            foundation: Number($('#weightFoundation').val()) || 0,
            carbonation_upper: Number($('#weightCarbonationUpper').val()) || 0,
            carbonation_lower: Number($('#weightCarbonationLower').val()) || 0
        };

        console.log('저장할 가중치:', weights);

        $.ajax({
            url: '/api/save_evaluation_weights',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                filename: currentFilename,
                weights: weights
            }),
            success: function(response) {
                if (response.success) {
                    showSnackMessage('가중치가 저장되었습니다.');
                    console.log('가중치 저장 성공:', response);
                } else {
                    showSnackMessage('가중치 저장에 실패했습니다: ' + response.error);
                }
            },
            error: function(xhr, status, error) {
                console.error('가중치 저장 요청 실패:', error);
                showSnackMessage('가중치 저장 중 오류가 발생했습니다.');
            }
        });
    }




    // 폼 초기화 함수
    function resetForm() {
        console.log('폼 초기화');
        document.getElementById('length').value = '';
        document.getElementById('width').value = '';
        document.getElementById('structureType').value = '';
        document.getElementById('spanCount').value = '';
        document.getElementById('expansionJointLocations').value = '';

        // 카드들 숨기기
        document.getElementById('componentSelectionCard').style.display = 'none';
        document.getElementById('evaluationResults').style.display = 'none';

        // 데이터 초기화
        bridgeData = {
            name: '',
            structureType: '',
            length: 0,
            width: 0,
            spanCount: 0,
            expansionJointLocations: '',
            spans: []
        };

        damageData = {
            slab: [],
            girder: [],
            crossbeam: [],
            abutment: [],
            pier: [],
            foundation: [],
            bearing: [],
            expansionJoint: [],
            pavement: [],
            drainage: [],
            railing: []
        };
    }

    // 손상 데이터 처리 함수
    function processDamageData(damageDataFromServer) {
        console.log('손상 데이터 처리 시작:', damageDataFromServer);

        // 부재명 정규화 매핑
        const componentMapping = {
            '바닥판': 'slab',
            '거더': 'girder',
            '가로보': 'crossbeam',
            '교대': 'abutment',
            '교각': 'pier',
            '교량받침': 'bearing',
            '받침': 'bearing',
            '신축이음': 'expansionJoint',
            '이음장치': 'expansionJoint',
            '교면포장': 'pavement',
            '포장': 'pavement',
            '배수시설': 'drainage',
            '배수구': 'drainage',
            '난간': 'railing',
            '연석': 'railing',
            '방호울타리': 'railing',
            '방호벽': 'railing',
            '방음벽': 'railing',
            '중분대': 'railing',
            '중앙분리대': 'railing',
            '낙석방지망': 'railing',
            '방음판': 'railing',
            '차광망': 'railing',
            '낙석방지책': 'railing',
            '경계석': 'railing',
            '가드레일': 'railing',
            '안전난간': 'railing',
            '보행자난간': 'railing',
            '차량방호울타리': 'railing',
            '중앙분리난간': 'railing',
            '측면방호울타리': 'railing',
            '원형난간': 'railing',
            '사각난간': 'railing',
            '방호시설': 'railing',
            '안전시설': 'railing',
            '교량난간': 'railing',
            '보도난간': 'railing',
            '차도난간': 'railing',
            '콘크리트난간': 'railing',
            '강재난간': 'railing',
            '알루미늄난간': 'railing',
            '스테인리스난간': 'railing',
            '복합난간': 'railing',
            '투명난간': 'railing',
            '유리난간': 'railing',
            '펜스': 'railing',
            '울타리': 'railing',
            '방벽': 'railing',
            '차선분리대': 'railing',
            '중앙분리시설': 'railing',
            '중분': 'railing',
            'GP': 'railing',
            'GP난간': 'railing',
            '가드파이프': 'railing',
            '가이드포스트': 'railing',
            '반사경': 'railing',
            '시선유도시설': 'railing',
            '충격흡수시설': 'railing',
            '완충시설': 'railing',
            '낙하물방지망': 'railing',
            '안전망': 'railing',
            '보호망': 'railing',
            '차량충돌방지시설': 'railing',
            '추락방지난간': 'railing',
            '안전울타리': 'railing',
            '보안울타리': 'railing',
            '차폐울타리': 'railing',
            '철책': 'railing',
            '철망': 'railing',
            '와이어메쉬': 'railing',
            '망사': 'railing',
            'SUS난간': 'railing',
            '파이프난간': 'railing',
            '앵글난간': 'railing',
            '각관난간': 'railing',
            '원형관난간': 'railing',
            '조립식난간': 'railing',
            '프리캐스트난간': 'railing',
            '현장타설난간': 'railing',
            '볼트체결난간': 'railing',
            '용접난간': 'railing',
            '연속난간': 'railing',
            '단속난간': 'railing',
            '금속난간': 'railing',
            '비금속난간': 'railing',
            '복합재난간': 'railing',
            '플라스틱난간': 'railing',
            'FRP난간': 'railing',
            '고무난간': 'railing',
            '목재난간': 'railing',
            '석재난간': 'railing',
            '조화블록': 'railing',
            '식생블록': 'railing'
        };

        // damageData 초기화
        damageData = {
            slab: [],
            girder: [],
            crossbeam: [],
            abutment: [],
            pier: [],
            foundation: [],
            bearing: [],
            expansionJoint: [],
            pavement: [],
            drainage: [],
            railing: []
        };

        // 서버에서 받은 데이터를 처리
        Object.keys(damageDataFromServer).forEach(componentName => {
            const normalizedComponent = findComponentType(componentName, componentMapping);

            if (normalizedComponent && damageDataFromServer[componentName]) {
                damageDataFromServer[componentName].forEach(item => {
                    damageData[normalizedComponent].push({
                        spanId: item.position,
                        type: normalizedComponent,
                        damageType: item.damage_type,
                        damageQuantity: item.damage_quantity,
                        count: item.count,
                        unit: item.unit,
                        inspectionArea: item.inspection_area || 0
                    });
                });
            }
        });

        console.log('처리된 손상 데이터:', damageData);
        return damageData;
    }

    // 부재 타입 찾기 함수
    function findComponentType(componentName, mapping) {
        // 정확한 매칭 먼저 시도
        if (mapping[componentName]) {
            return mapping[componentName];
        }

        // 부분 매칭 시도
        for (const [key, value] of Object.entries(mapping)) {
            if (componentName.includes(key) || key.includes(componentName)) {
                return value;
            }
        }

        console.warn('매핑되지 않은 부재명:', componentName);
        return null;
    }

    $('#generateSpans').on('click', function() {
        console.log("저장 버튼 클릭됨");

        // 입력값 가져오기
        const bridgeSelect = $('#bridgeName');
        const selectedOption = bridgeSelect.find('option:selected');
        const bridgeName = selectedOption.text() || selectedOption.val();
        const structureType = $('#structureType').val();
        const spanCount = parseInt($('#spanCount').val());
        const length = parseFloat($('#length').val());
        const width = parseFloat($('#width').val());
        const expansionJointLocations = $('#expansionJointLocations').val();
        const fileId = bridgeSelect.val();

        // fileId(교량명) 선택 여부 체크
        if (!fileId) {
            showSnackMessage('교량명을 선택해주세요.');
            return;
        }

        // 입력값 검증
        if (!bridgeName || !structureType || isNaN(spanCount) || isNaN(length) || isNaN(width)) {
            showSnackMessage('모든 필수 필드를 입력해주세요.');
            return;
        }

        if (spanCount < 1) {
            showSnackMessage('경간 수는 1 이상이어야 합니다.');
            return;
        }

        // 1. 교량 정보 서버에 저장 (update_bridge_info 호출)
        $.ajax({
            url: '/api/update_bridge_info',
            method: 'POST',
            data: {
                file_id: fileId,
                bridge_name: bridgeName,
                structure_type: structureType,
                span_count: spanCount,
                length: length,
                width: width,
                expansion_joint_location: expansionJointLocations
            },
            success: function(response) {

                alert('교량 정보 저장 성공');
                loadSavedBridges();

                if (response.success) {
                    console.log('교량 정보 저장 성공');
                    response.message && showSnackMessage(response.message);
                } else {
                    showSnackMessage('교량 정보 저장 실패: ' + (response.error || '알 수 없는 오류'));
                }

                 // 교량 목록 다시 로드
            },
            error: function(xhr, status, error) {
                showSnackMessage('교량 정보 저장 중 오류가 발생했습니다.');
            }
        });

        // 2. 기존 로컬 처리 로직 계속 실행
        bridgeData = {
            name: bridgeName,
            structureType: structureType,
            length: length,
            width: width,
            spanCount: spanCount,
            expansionJointLocations: expansionJointLocations,
            spans: []
        };

        generateSpansData(spanCount);
        saveBridgeData();
        $('#componentSelectionCard').show();
        $('#bridgeListCard').show();

        console.log("교량 데이터 생성 완료:", bridgeData);
    });


    /*
    // 경간 생성 버튼 클릭 이벤트
    $('#generateSpans').on('click', function() {
        console.log("저장 버튼 클릭됨");

        // 입력값 가져오기
        const bridgeSelect = $('#bridgeName');
        const selectedOption = bridgeSelect.find('option:selected');
        const bridgeName = selectedOption.text() || selectedOption.val(); // 표시 텍스트를 우선으로, 없으면 값 사용
        const structureType = $('#structureType').val();
        const spanCount = parseInt($('#spanCount').val());
        const length = parseFloat($('#length').val());
        const width = parseFloat($('#width').val());
        const expansionJointLocations = $('#expansionJointLocations').val();

        // 입력값 검증
        if (!bridgeName || !structureType || isNaN(spanCount) || isNaN(length) || isNaN(width)) {
            showSnackMessage('모든 필수 필드를 입력해주세요.');
            return;
        }

        if (spanCount < 1) {
            showSnackMessage('경간 수는 1 이상이어야 합니다.');
            return;
        }

        // 교량 데이터 설정
        bridgeData = {
            name: bridgeName,
            structureType: structureType,
            length: length,
            width: width,
            spanCount: spanCount,
            expansionJointLocations: expansionJointLocations,
            spans: []
        };

        // 경간 데이터 생성
        generateSpansData(spanCount);

        // 교량 데이터 저장
        saveBridgeData();

        // 다음 단계 보여주기
        $('#componentSelectionCard').show();
        $('#bridgeListCard').show();

        console.log("교량 데이터 생성 완료:", bridgeData);
    });
    */
    // 교량 데이터 저장 함수
    function saveBridgeData() {
        try {
            // 이미 존재하는 교량인지 확인
            const existingIndex = savedBridges.findIndex(bridge => bridge.name === bridgeData.name);

            if (existingIndex !== -1) {
                // 기존 데이터 업데이트
                savedBridges[existingIndex] = bridgeData;
            } else {
                // 새로운 데이터 추가
                savedBridges.push(bridgeData);
            }

            // 로컬 스토리지에 저장
            localStorage.setItem('savedBridges', JSON.stringify(savedBridges));
            console.log('교량 데이터 저장 완료:', savedBridges);

            // 리스트 업데이트
            updateBridgeList();
        } catch (error) {
            console.error('교량 데이터 저장 중 오류 발생:', error);
            showSnackMessage('교량 데이터 저장 중 오류가 발생했습니다.');
        }
    }

    // 교량 리스트 업데이트 함수
    async function updateBridgeList(){
        const tbody = $('#bridgeListTable tbody');
        tbody.empty();

        if (savedBridges.length === 0) {
            tbody.append('<tr><td colspan="7" class="text-center">저장된 교량 데이터가 없습니다.</td></tr>');
        } else {
            savedBridges.forEach((bridge, index) => {
                const isSelected = bridgeData && bridgeData.name === bridge.name;
                const row = `
                    <tr title='교량 기본정보 조회' data-index="${index}" class="bridge-row ${isSelected ? 'table-primary' : ''}" style="cursor: pointer; background-color: ${isSelected ? '' : '#ffffff'};">
                        <td>${bridge.name}</td>
                        <td>${bridge.structureType}</td>
                        <td>${bridge.length}</td>
                        <td>${bridge.width}</td>
                        <td>${bridge.spanCount}</td>
                        <!--
                        <td>${bridge.expansionJointLocations}</td>
                        -->

                    </tr>
                `;
                tbody.append(row);
            });
        }

        // 교량 리스트 테이블 표시
        $('#bridgeListCard').show();

        // 교량 행 클릭 이벤트
        $('.bridge-row').on('click', function(e) {
            // 수정/삭제 버튼 클릭 시 이벤트 전파 중단

            // 이전 선택된 행의 하이라이트 제거
            $('.bridge-row').removeClass('table-primary').css('background-color', '#ffffff');

            // 현재 선택된 행 하이라이트
            $(this).addClass('table-primary').css('background-color', '');

            const index = $(this).data('index');
            const bridge = savedBridges[index];


            console.log('저장된 교량 선택:', bridge.name);

            // 현재 선택된 교량 데이터 설정
            bridgeData = bridge;

            // 부재 체크박스는 loadComponentSelection()에서 복원됨
            // 기본적으로는 모든 부재를 선택하지 않음 (저장된 데이터 우선)

            // 기초 체크박스가 선택된 경우 노출된 기초 위치 입력 필드 표시 (나중에 복원될 때 처리됨)
            // if ($('#foundationCheck').is(':checked')) {
            //     $('#foundationExposedInput').show();
            // }

            // 신축이음 체크박스가 선택된 경우 신축이음 위치 입력 필드 표시 (나중에 복원될 때 처리됨)
            // if ($('#expansionJointCheck').is(':checked')) {
            //     $('#expansionJointLocationInput').show();
            // }

            // 부재 선택 카드 표시
            const componentCard = document.getElementById('componentSelectionCard');
            if (componentCard) {
                componentCard.style.display = 'block';
            }

            // 상태평가 생성
            const selectedComponents = {
                slab: true,
                girder: true,
                crossbeam: true,
                abutment: true,
                pier: true,
                foundation: true,
                bearing: true,
                expansionJoint: true,
                pavement: true,
                drainage: true,
                railing: true,
                carbonationUpper: $('#carbonationUpperCheck').is(':checked'),
                carbonationLower: $('#carbonationLowerCheck').is(':checked')
            };

            // 손상 데이터 생성
            //generateDamageData();

            // 선택된 부재에 대해서만 상태평가 생성


            // 통합 상태평가 생성
            //generateTotalEvaluationTable(selectedComponents);

            // 결과 섹션 표시



             console.log('저장된 교량 선택:', bridge.name);

            // 폼에 데이터 채우기
            // 교량명 드롭다운에서 해당 교량 찾기
            const bridgeSelect = $('#bridgeName');
            let optionFound = false;
            bridgeSelect.find('option').each(function() {
                if ($(this).text() === bridge.name) {
                    bridgeSelect.val($(this).val());
                    $('#bridgeNameInput').val($(this).text());
                    optionFound = true;
                    return false; // break
                }
            });





            if (optionFound) {
                // 교량 데이터 로드
                const selectedFilename = bridgeSelect.val();
                if (selectedFilename) {
                    loadBridgeData(selectedFilename);
                    window.currentSelectedFilename = selectedFilename;
                    window.currentFileId = selectedFilename; // currentFileId도 설정

                    // 부재 선택 데이터 불러오기
                    loadComponentSelection();

                    // 가중치 불러오기
                    loadEvaluationWeights();

                    //alert('현재 선택된 파일명: ' + window.currentSelectedFilename);
                    console.log('현재 선택된 파일명:', window.currentSelectedFilename);

                }
            } else {
                // 드롭다운에 없는 경우 직접 설정
                document.getElementById('structureType').value = bridge.structureType;
                document.getElementById('spanCount').value = bridge.spanCount;
                document.getElementById('length').value = bridge.length;
                document.getElementById('width').value = bridge.width;
                document.getElementById('expansionJointLocations').value = bridge.expansionJointLocations;
            }

            // 현재 선택된 교량 데이터 설정
            bridgeData = bridge;



            // 부재 선택 카드 표시


        });

        // 수정 버튼 이벤트
        $('.edit-bridge').on('click', function() {
            const index = $(this).data('index');
            const bridge = savedBridges[index];

            console.log('저장된 교량 선택:', bridge.name);

            // 폼에 데이터 채우기
            // 교량명 드롭다운에서 해당 교량 찾기
            const bridgeSelect = $('#bridgeName');
            let optionFound = false;
            bridgeSelect.find('option').each(function() {
                if ($(this).text() === bridge.name) {
                    bridgeSelect.val($(this).val());
                    optionFound = true;
                    return false; // break
                }
            });

            if (optionFound) {
                // 교량 데이터 로드
                const selectedFilename = bridgeSelect.val();
                if (selectedFilename) {
                    loadBridgeData(selectedFilename);
                    window.currentSelectedFilename = selectedFilename;
                    window.currentFileId = selectedFilename;

                    // 부재 선택 데이터 불러오기
                    loadComponentSelection();

                    // 가중치 불러오기
                    loadEvaluationWeights();
                }
            } else {
                // 드롭다운에 없는 경우 직접 설정
                document.getElementById('structureType').value = bridge.structureType;
                document.getElementById('spanCount').value = bridge.spanCount;
                document.getElementById('length').value = bridge.length;
                document.getElementById('width').value = bridge.width;
                document.getElementById('expansionJointLocations').value = bridge.expansionJointLocations;
            }

            // 현재 선택된 교량 데이터 설정
            bridgeData = bridge;

            // 부재 선택 카드 표시
            const componentCard = document.getElementById('componentSelectionCard');
            if (componentCard) {
                componentCard.style.display = 'block';
            }
        });

        // 삭제 버튼 이벤트
        $('.delete-bridge').on('click', function() {
            const index = $(this).data('index');
            if (confirm('정말로 이 교량 데이터를 삭제하시겠습니까?')) {
                savedBridges.splice(index, 1);
                localStorage.setItem('savedBridges', JSON.stringify(savedBridges));
                updateBridgeList();
            }
        });
    }

    // 경간 데이터 생성 함수
    function generateSpansData(spanCount) {
        bridgeData.spans = [];

        // 첫 번째 교대(A1) 추가
        bridgeData.spans.push({
            id: 'A1',
            type: 'abutment',
            length: 0
        });

        // 경간별 교각 및 거더 추가
        const spanLength = bridgeData.length / spanCount;

        for (let i = 1; i <= spanCount; i++) {
            // 거더 추가
            bridgeData.spans.push({
                id: `S${i}`,
                type: 'span',
                length: spanLength
            });

            // 마지막 경간이 아니면 교각 추가
            if (i < spanCount) {
                bridgeData.spans.push({
                    id: `P${i}`,
                    type: 'pier',
                    length: 0
                });
            }
        }

        // 마지막 교대(A2) 추가
        bridgeData.spans.push({
            id: 'A2',
            type: 'abutment',
            length: 0
        });

        console.log("생성된 경간 데이터:", bridgeData.spans);
    }

    // 상태평가 생성 버튼 클릭 이벤트
    $('#generateEvaluation').on('click', async function() {
        updateSlabEvaluationTable(bridgeData.id, true);
        //await showLoadingEvalution(true);
        saveEvaluationWeights();
        console.log("상태평가 생성 버튼 클릭됨");

    });


    showLoadingEvalution = async function( initvalue) {
         showLoading();
        console.log("상태평가 생성 버튼 클릭됨");

        // 선택된 부재 확인
        const selectedComponents = {
            slab: $('#slabCheck').is(':checked'),
            girder: $('#girderCheck').is(':checked'),
            crossbeam: $('#crossbeamCheck').is(':checked'),
            abutment: $('#abutmentCheck').is(':checked'),
            pier: $('#pierCheck').is(':checked'),
            foundation: $('#foundationCheck').is(':checked'),
            bearing: $('#bearingCheck').is(':checked'),
            expansionJoint: $('#expansionJointCheck').is(':checked'),
            pavement: $('#pavementCheck').is(':checked'),
            drainage: $('#drainageCheck').is(':checked'),
            railing: $('#railingCheck').is(':checked'),
            carbonationUpper: $('#carbonationUpperCheck').is(':checked'),
            carbonationLower: $('#carbonationLowerCheck').is(':checked')
            };
            for (const [key, isChecked] of Object.entries(selectedComponents)) {
                if (isChecked) {
                    $("a[href='#" + key + "EvaluationHeader']").css('display', 'block');
                } else {
                    $("a[href='#" + key + "EvaluationHeader']").css('display', 'none');
                }
            }
        console.log('선택된 부재들:', selectedComponents);

        // 부재 선택 데이터 저장
        saveComponentSelection();

        // 현재 선택된 파일명 가져오기
        const currentFilename = window.currentSelectedFilename;
        if (!currentFilename) {
            showSnackMessage('교량을 먼저 선택해주세요.');
            hideLoading();
            return;
        }

        try {
            // 서버에서 상태평가 데이터 생성 요청
            showResponseData = await $.ajax({
                url: '/api/generate_evaluation_data',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    filename: currentFilename
                })
            });


            if (!showResponseData.success) {
                console.error('상태평가 데이터 생성 실패:', showResponseData.error);
                showSnackMessage('상태평가 데이터 생성에 실패했습니다: ' + showResponseData.error);
                hideLoading();
                return;
            }

            // 서버에서 받은 데이터로 damageData 업데이트
            damageData = showResponseData.data;
            damageDataStr= JSON.stringify(showResponseData.data);

            // 선택된 부재에 대해서만 상태평가 생성
            Object.entries(selectedComponents).forEach(([component, isSelected]) => {
                const card = document.getElementById(`${component}EvaluationCard`);
                if (isSelected) {
                    console.log(`${component} 상태평가 생성 중...`);
                    const componentDamageData = damageData[component] || [];
                    //alert(component);
                    // 부재별 테스트 할때 처리 로직 위해 잠시 수정 함
                    if(component=='girder'){
                        console.log(componentDamageData);
                        generateEvaluationTable(component, componentDamageData);
                    } else {
                        generateEvaluationTable(component, componentDamageData);
                    }

                    if (card) {
                        card.style.display = 'block';
                        console.log(`${component}EvaluationCard 표시됨`);
                    }
                } else {
                    if (card) {
                        card.style.display = 'none';
                    }
                }
            });

            // 통합 상태평가 생성
            generateTotalEvaluationTable(selectedComponents);

            // 결과 섹션 표시
            const resultsDiv = document.getElementById('evaluationResults');
            if (resultsDiv) {
                resultsDiv.style.display = 'block';
                console.log('상태평가 결과 섹션 표시됨');
            }

            // 통합산정결과표 카드 표시
            const totalEvaluationCard = document.getElementById('totalEvaluationCard');
            if (totalEvaluationCard) {
                totalEvaluationCard.style.display = 'block';
                console.log('통합산정결과표 카드 표시됨');
            }
            showSnackMessage("상태평가 생성 완료되었습니다.");


              // ...기존 코드...

              // ㅎinput[type="number"] 값이 변경될 때 이벤트 처리


              // ...기존 코드...
            $(document).off('keydown', 'input[type="number"]');

            $(document).on('keydown', 'input[type="number"]', function (e) {
                if (e.key === 'Enter') {
                    e.preventDefault(); // 기본 Enter 동작 방지

                    const $this = $(this);

                    // // area-input 클래스를 가진 면적 입력 필드인지 확인
                    // if ($this.hasClass('area-input')) {
                    //     // 면적 입력 필드의 경우 로컬에서만 계산 처리
                    //     const newArea = parseFloat($this.val()) || 100;
                    //     const $row = $this.closest('tr');
                    //     const spanId = $row.find('td:first').text();

                    //     console.log(`${spanId} 면적 변경: ${newArea} (엔터키로 확정)`);

                    //     // 해당 행의 비율 재계산 및 등급 업데이트 (로컬에서만)
                    //     updateRowCalculations($row, newArea);

                    //     // 포커스를 다음 입력 필드로 이동
                    //     $this.blur();
                    // } else {
                    //     // 다른 number 입력 필드의 경우 기존 로직 실행
                    //    // updateSlabEvaluationTable(bridgeData.id, false);
                    // }

                    $this.blur();


                    //saveandreplace(this);




                        var table = $(this).closest('.card').find('table').get(0);
                        //var type = "slab"; // 버튼의 data-type 속성 값 가져오기

                        if (table && table.id) {
                        type = table.id.replace('EvaluationTable', '');
                        }


                        if (!table) {
                        alert('바닥판 상태평가가 없습니다.');
                        return;
                        }

                        const rows = table.querySelectorAll('tbody tr');
                        const damage_list = [];

                        rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length < 1) return;

                        // 실제 테이블 구조에 맞게 인덱스 조정 필요
                        const spanId = cells[0]?.innerText.trim() || '';
                        const damageType =  '균열';
                        const damageQuantity = getRandomDamageValue(1, 5); // 임의의 손상량 생성 함수
                        const count ='1'; // 실제 데이터에 따라 조정
                        const unit =  'm';
                        const inspectionArea = cells[1]?.querySelector('input')?.value.trim() || '';
                        damage_list.push({
                        "count": count,
                            "damageQuantity": damageQuantity,
                            "damageType": damageType,
                            "inspectionArea": inspectionArea,
                            "spanId": spanId,
                            "type": type,
                            "unit": unit,
                            "updatedAt": new Date().toISOString()
                        });
                        });
                        get_span_damage = damage_list;
                        console.log('수정된 손상 데이터:', get_span_damage);

                        showLoadingEvalutionForSaved( true);

            }
        });



            const $results = $('#evaluationResults');
            if (initvalue && $results.length) {
                // 결과 카드의 중간 위치로 스크롤
                $('html, body').animate({
                    scrollTop: $results.offset().top -100
                }, 1000);
            }

            hideLoading();
            console.log("상태평가 생성 완료");
        } catch (error) {
            console.error('상태평가 데이터 생성 요청 실패:', error);
            showSnackMessage('상태평가 데이터 생성 요청에 실패했습니다.');
        } finally {
            hideLoading();
        }
    };




     showLoadingEvalutionForSaved = async function( initvalue) {
         //  showLoading();
        console.log("상태평가 생성 버튼 클릭됨 (저장된 데이터용)");

        // 선택된 부재 확인
        const selectedComponents = {
            slab: $('#slabCheck').is(':checked'),
            girder: $('#girderCheck').is(':checked'),
            crossbeam: $('#crossbeamCheck').is(':checked'),
            abutment: $('#abutmentCheck').is(':checked'),
            pier: $('#pierCheck').is(':checked'),
            foundation: $('#foundationCheck').is(':checked'),
            bearing: $('#bearingCheck').is(':checked'),
            expansionJoint: $('#expansionJointCheck').is(':checked'),
            pavement: $('#pavementCheck').is(':checked'),
            drainage: $('#drainageCheck').is(':checked'),
            railing: $('#railingCheck').is(':checked'),
            carbonationUpper: $('#carbonationUpperCheck').is(':checked'),
            carbonationLower: $('#carbonationLowerCheck').is(':checked')
            };

        console.log('선택된 부재들:', selectedComponents);

        // 부재 선택 데이터 저장
        //saveComponentSelection();

        // 현재 선택된 파일명 가져오기
        const currentFilename = window.currentSelectedFilename;
        if (!currentFilename) {
            showSnackMessage('교량을 먼저 선택해주세요.');
            return;
        }

        try {
            // 캐시된 데이터 사용 (damageDataStr을 통해 복원)
            if (damageDataStr && damageDataStr.trim() !== '') {
                console.log('캐시된 damageDataStr 사용');
                damageData = JSON.parse(damageDataStr);
            } else if (showResponseData && showResponseData.success && showResponseData.data) {
                console.log('showResponseData에서 데이터 복원');
                damageData = JSON.parse(JSON.stringify(showResponseData.data));
                damageDataStr = JSON.stringify(showResponseData.data);
            } else {
                console.log('캐시된 데이터가 없어서 함수 종료');
                showSnackMessage('상태평가 데이터가 없습니다. 먼저 상태평가를 생성해주세요.');
                return;
            }

            console.log('사용할 damageData:', damageData);

            // 선택된 부재에 대해서만 상태평가 생성
            Object.entries(selectedComponents).forEach(([component, isSelected]) => {
                const card = document.getElementById(`${component}EvaluationCard`);
                if (isSelected) {
                    console.log(`${component} 상태평가 생성 중...`);
                    const componentDamageData = damageData[component] || [];
                    generateEvaluationTable(component, componentDamageData);
                    if (card) {
                        card.style.display = 'block';
                        console.log(`${component}EvaluationCard 표시됨`);
                    }
                } else {
                    if (card) {
                        card.style.display = 'none';
                    }
                }
            });

        } catch (error) {
            console.error('저장된 상태평가 데이터 처리 실패:', error);
            showSnackMessage('저장된 상태평가 데이터 처리에 실패했습니다.');
        }
    };
    // 출력 버튼 클릭 이벤트


    // 저장 버튼 클릭 이벤트
    $('#saveEvaluation').on('click', function() {
        saveEvaluationResults();
    });

    // 상태평가 결과 저장 함수
    function saveEvaluationResults() {
        const currentFilename = window.currentSelectedFilename;
        if (!currentFilename) {
            showSnackMessage('교량을 먼저 선택해주세요.');
            return;
        }

        // 현재 상태평가 결과 수집
        const evaluationData = {
            timestamp: new Date().toISOString(),
            bridge_name: document.getElementById('bridgeName').value,
            structure_type: document.getElementById('structureType').value,
            component_results: {}
        };

        // 각 부재별 결과 수집
        const componentTypes = ['slab', 'girder', 'crossbeam', 'abutment', 'pier', 'foundation', 'bearing', 'expansionJoint', 'pavement', 'drainage', 'railing'];

        componentTypes.forEach(component => {
            const table = document.getElementById(`${component}EvaluationTable`);
            if (table && table.style.display !== 'none') {
                const rows = table.querySelectorAll('tbody tr');
                const componentResults = [];

                rows.forEach(row => {
                    const cells = row.cells;
                    if (cells.length > 0) {
                        const spanId = cells[0].textContent;
                        const grade = cells[cells.length - 1].textContent;
                        componentResults.push({
                            span_id: spanId,
                            grade: grade
                        });
                    }
                });

                evaluationData.component_results[component] = componentResults;
            }
        });

        // 서버에 저장 요청
        $.ajax({
            url: '/api/save_evaluation_result',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                filename: currentFilename,
                evaluation_data: evaluationData
            }),
            success: function(response) {
                if (response.success) {
                    showSnackMessage('상태평가 결과가 저장되었습니다.');
                } else {
                    showSnackMessage('저장에 실패했습니다: ' + response.error);
                }
            },
            error: function(xhr, status, error) {
                console.error('저장 요청 실패:', error);
                showSnackMessage('저장 요청에 실패했습니다.');
            }
        });
    }

    // 부재별 집계표 데이터를 활용한 손상 데이터 생성
    function generateDamageData() {
        console.log('손상 데이터 생성 시작');

        // damageData 초기화
        damageData = {
            slab: [],
            girder: [],
            crossbeam: [],
            abutment: [],
            pier: [],
            bearing: [],
            expansionJoint: [],
            pavement: [],
            drainage: [],
            railing: []
        };

        // 교량 경간에 따른 부재별 손상 데이터 생성 psk-0616
        for (let i = 0; i < bridgeData.spans.length - 1; i++) {
            const spanId = bridgeData.spans[i].id;

            // 바닥판 손상 데이터
            damageData.slab.push({
                spanId: spanId,
                type: 'slab',
                damageType: '균열',
                damageQuantity: getRandomDamageValue(1, 5),
                count: 1,
                unit: 'm',
                inspectionArea: 100
            });

            // 거더 손상 데이터
            damageData.girder.push({
                spanId: spanId,
                type: 'girder',
                damageType: '균열',
                damageQuantity: getRandomDamageValue(1, 3),
                count: 1,
                unit: 'm',
                inspectionArea: 100
            });

            // 가로보 손상 데이터
            damageData.crossbeam.push({
                spanId: spanId,
                type: 'crossbeam',
                damageType: '균열',
                damageQuantity: getRandomDamageValue(1, 2),
                count: 1,
                unit: 'm',
                inspectionArea: 100
            });

            // 교대 손상 데이터
            if (spanId.startsWith('A')) {
                damageData.abutment.push({
                    spanId: spanId,
                    type: 'abutment',
                    damageType: '균열',
                    damageQuantity: getRandomDamageValue(1, 3),
                    count: 1,
                    unit: 'm',
                    inspectionArea: 100
                });
            }

            // 교각 손상 데이터
            if (spanId.startsWith('P')) {
                damageData.pier.push({
                    spanId: spanId,
                    type: 'pier',
                    damageType: '균열',
                    damageQuantity: getRandomDamageValue(1, 3),
                    count: 1,
                    unit: 'm',
                    inspectionArea: 100
                });

                // 기초 손상 데이터
                damageData.foundation.push({
                    spanId: spanId,
                    type: 'foundation',
                    damageType: '균열',
                    damageQuantity: getRandomDamageValue(1, 3),
                    count: 1,
                    unit: 'm',
                    inspectionArea: 100
                });
            }

            // 교량받침 손상 데이터
            damageData.bearing.push({
                spanId: spanId,
                type: 'bearing',
                damageType: '파손',
                damageQuantity: getRandomDamageValue(1, 2),
                count: 1,
                unit: '개',
                inspectionArea: 100
            });

            // 신축이음 손상 데이터
            if (spanId.startsWith('A') || spanId.startsWith('P')) {
                damageData.expansionJoint.push({
                    spanId: spanId,
                    type: 'expansion_joint',
                    damageType: '파손',
                    damageQuantity: getRandomDamageValue(1, 2),
                    count: 1,
                    unit: '개',
                    inspectionArea: 100
                });
            }

            // 포장 손상 데이터
            damageData.pavement.push({
                spanId: spanId,
                type: 'pavement',
                damageType: '파손',
                damageQuantity: getRandomDamageValue(1, 5),
                count: 1,
                unit: 'm²',
                inspectionArea: 100
            });

            // 배수시설 손상 데이터
            damageData.drainage.push({
                spanId: spanId,
                type: 'drainage',
                damageType: '파손',
                damageQuantity: getRandomDamageValue(1, 2),
                count: 1,
                unit: '개',
                inspectionArea: 100
            });

            // 난간 손상 데이터
            damageData.railing.push({
                spanId: spanId,
                type: 'railing',
                damageType: '파손',
                damageQuantity: getRandomDamageValue(1, 2),
                count: 1,
                unit: 'm',
                inspectionArea: 100
            });
        }

        console.log("손상 데이터 생성 완료:", damageData);
    }

    // 면적 입력 이벤트 리스너 추가
    function addAreaInputListeners() {
        // change 이벤트: 값이 변경되고 포커스가 벗어날 때 (탭 이동 포함)
        $(document).on('change', '.area-input', function() {
            const $this = $(this);
            const newArea = parseFloat($this.val()) || 100;
            const $row = $this.closest('tr');
            const spanId = $row.find('td:first').text();

            console.log(`${spanId} 면적 변경: ${newArea} (change 이벤트)`);

            // 해당 행의 비율 재계산 및 등급 업데이트 (로컬에서만)
            updateRowCalculations($row, newArea);
        });

        // blur 이벤트: 포커스를 잃을 때도 처리 (추가 안전장치)
        $(document).on('blur', '.area-input', function() {
            const $this = $(this);
            const newArea = parseFloat($this.val()) || 100;
            const $row = $this.closest('tr');
            const spanId = $row.find('td:first').text();

            console.log(`${spanId} 면적 변경: ${newArea} (blur 이벤트)`);

            // 해당 행의 비율 재계산 및 등급 업데이트 (로컬에서만)
            updateRowCalculations($row, newArea);
        });

        // 배수시설 테이블 변경 감지 및 포장 테이블 업데이트 (디바운싱 적용)
        $(document).on('DOMSubtreeModified change input', '#drainageEvaluationTable', function() {
            // 무한루프 방지
            if (isUpdatingPavementDrainage) {
                return;
            }

            console.log('배수시설 테이블 변경 감지');

            // 기존 타이머 제거 (디바운싱)
            if (drainageUpdateTimeout) {
                clearTimeout(drainageUpdateTimeout);
            }

            // 새 타이머 설정
            drainageUpdateTimeout = setTimeout(function() {
                updatePavementDrainageFromDrainageTable();
                drainageUpdateTimeout = null;
            }, 300); // 300ms 지연으로 디바운싱
        });

        // MutationObserver를 사용한 더 안정적인 감지 (최신 브라우저)
        if (typeof MutationObserver !== 'undefined') {
            const drainageTable = document.getElementById('drainageEvaluationTable');
            if (drainageTable) {
                const observer = new MutationObserver(function(mutations) {
                    // 무한루프 방지
                    if (isUpdatingPavementDrainage) {
                        return;
                    }

                    let shouldUpdate = false;
                    mutations.forEach(function(mutation) {
                        if (mutation.type === 'childList' || mutation.type === 'characterData') {
                            shouldUpdate = true;
                        }
                    });

                    if (shouldUpdate) {
                        console.log('배수시설 테이블 MutationObserver 변경 감지');

                        // 기존 타이머 제거 (디바운싱)
                        if (drainageUpdateTimeout) {
                            clearTimeout(drainageUpdateTimeout);
                        }

                        // 새 타이머 설정
                        drainageUpdateTimeout = setTimeout(function() {
                            updatePavementDrainageFromDrainageTable();
                            drainageUpdateTimeout = null;
                        }, 300); // 300ms 지연으로 디바운싱
                    }
                });

                observer.observe(drainageTable, {
                    childList: true,
                    subtree: true,
                    characterData: true
                });
            }
        }
    }
    function extractExpansionJointFlags(data) {
            const bodyCondition = data.body_condition || '';
            const notes = data.expansion_joint_notes || '';
            const combinedText = `${bodyCondition} ${notes}`.toLowerCase();
            return {
                aging_or_dirt: /토사|이물질|퇴적|균열|침적|끼임/.test(combinedText),
                function_degradation: /불량|물받이|볼트|너트|탈락|부식|파손|박리|박락|누수|기울어짐|기능저하|변형/.test(combinedText),
                impact_or_noise: /강판|이상음|밀착|거동|지장|충격|심한파손|심한단차|진동|소음|차량통과/.test(combinedText),
                structural_damage: /본체파손|본체탈락|작동불능|금속부재탈락|구조적손상|완전파괴/.test(combinedText),
                other_damage: /기타|기준외|특이사항/.test(combinedText)
            };
    }
    // 행의 계산 업데이트
    function updateRowCalculations($row, newArea) {
        const $cells = $row.find('td');

        // 테이블 헤더로부터 부재 타입 확인
        const $table = $row.closest('table');
        const componentType = getComponentTypeFromTable($table);

        console.log(`계산 업데이트 시작 - 부재: ${componentType}, 면적: ${newArea}`);

        // 부재별로 다른 계산 로직 적용
        // 신축이음 상태평가 플래그 추출 함수 (상위 스코프로 이동)

        //alert('면적이 변경되었습니다. 해당 부재의 손상 비율과 등급을 자동으로 업데이트합니다.');

        switch(componentType) {
            case 'slab':
                // 바닥판 타입 확인 (강바닥판인지 일반 바닥판인지)
                const slabType = $("#slabType").val();
                if (slabType === 'STEEL') {

                    updateSteelSlabCalculations($row, $cells, newArea);
                } else {

                    updateSlabGirderCalculations($row, $cells, newArea);
                }
                break;
            case 'girder':
                updateSlabGirderCalculations($row, $cells, newArea);
                break;
            case 'crossbeam':
                updateCrossbeamCalculations($row, $cells, newArea);
                break;
            case 'abutment':
                updateAbutmentCalculations($row, $cells, newArea);
                break;
            case 'pier':
                updatePierCalculations($row, $cells, newArea);
                break;
            case 'pavement':
                updatePavementCalculations($row, $cells, newArea);
                break;
            case 'railing':
                updateRailingCalculations($row, $cells, newArea);
                break;
            default:
                console.log(`지원되지 않는 부재 타입: ${componentType}`);
                break;
        }

        // 최종 등급 재계산
        updateFinalGrade($row);

        // 통합 상태평가 자동 업데이트
        updateTotalEvaluationTableIfVisible();
    }

    // 테이블로부터 부재 타입 추출
    function getComponentTypeFromTable($table) {
        const tableId = $table.attr('id');
        if (tableId) {
            // "slabEvaluationTable" -> "slab"
            return tableId.replace('EvaluationTable', '');
        }
        return null;
    }

    // 현재 행의 API 데이터 추출 헬퍼 함수
    function getCurrentRowApiData($row) {
        try {
            const spanId = $row.find('td:first').text().trim();
            const tableId = $row.closest('table').attr('id');

            // 현재 테이블의 데이터 캐시에서 해당 span 데이터 찾기
            if (window.currentEvaluationData) {
                const componentKey = getComponentKeyFromTableId(tableId);
                const componentData = window.currentEvaluationData[componentKey];
                if (componentData) {
                    return componentData.find(item => item.span_id === spanId);
                }
            }
            return null;
        } catch (e) {
            console.error('getCurrentRowApiData 오류:', e);
            return null;
        }
    }

    // 테이블 ID에서 컴포넌트 키 추출
    function getComponentKeyFromTableId(tableId) {
        const mapping = {
            'slabEvaluationTable': 'slab',
            'girderEvaluationTable': 'girder',
            'crossbeamEvaluationTable': 'crossbeam',
            'abutmentEvaluationTable': 'abutment',
            'pierEvaluationTable': 'pier',
            'foundationEvaluationTable': 'foundation',
            'bearingEvaluationTable': 'bearing',
            'expansionJointEvaluationTable': 'expansionJoint',
            'pavementEvaluationTable': 'pavement',
            'drainageEvaluationTable': 'drainage',
            'railingEvaluationTable': 'railing'
        };
        return mapping[tableId] || null;
    }



    // 바닥판/거더 계산 업데이트 (수정된 버전)
    function updateSlabGirderCalculations($row, $cells, newArea) {
        // 바닥판/거더 테이블 구조:
        // 경간, 점검면적, 1방향균열폭, 등급, 1방향균열율, 등급, 2방향균열폭, 등급, 2방향균열율, 등급, 누수면적율, 등급, 표면손상면적율, 등급, 철근부식면적율, 등급, 최종등급

        // 현재 행의 데이터 확인 (강 바닥판 vs 콘크리트 바닥판 구분)
        const rowData = getCurrentRowApiData($row);
        console.log(`행 데이터 확인:`, rowData);

        let crackData1d, crackData2d, leakData, surfaceData, rebarData;

        // 강 바닥판인 경우 (surface_deterioration_ratio가 있고 leak_ratio가 없는 경우)
        if (rowData && rowData.surface_deterioration_ratio !== undefined && !rowData.leak_ratio) {
            console.log('강 바닥판 데이터 처리 - original_damage_quantities에서 추출');

            // original_damage_quantities에서 직접 추출
            const originalQuantities = rowData.original_damage_quantities || {};
            console.log('Original quantities:', originalQuantities);

            crackData1d = extractOriginalDamageValue($cells.eq(4)); // 1방향 균열율 셀
            crackData2d = extractOriginalDamageValue($cells.eq(8)); // 2방향 균열율 셀

            // 누수와 철근부식을 original_damage_quantities에서 추출
            leakData = {
                hasData: (originalQuantities['누수'] || 0) > 0,
                value: originalQuantities['누수'] || 0
            };
            rebarData = {
                hasData: (originalQuantities['철근부식'] || 0) > 0,
                value: originalQuantities['철근부식'] || 0
            };
            // 표면손상은 기존 extractOriginalDamageValue 사용
            surfaceData = extractOriginalDamageValue($cells.eq(12));

            console.log('강 바닥판 추출된 데이터:', {leakData, rebarData});

        } else {
            console.log('콘크리트 바닥판 데이터 처리 (기존 방식)');

            // 콘크리트 바닥판의 경우 기존 방식 사용
            crackData1d = extractOriginalDamageValue($cells.eq(4)); // 1방향 균열율 셀
            crackData2d = extractOriginalDamageValue($cells.eq(8)); // 2방향 균열율 셀
            leakData = extractOriginalDamageValue($cells.eq(10)); // 누수 면적율 셀
            surfaceData = extractOriginalDamageValue($cells.eq(12)); // 표면손상 면적율 셀
            rebarData = extractOriginalDamageValue($cells.eq(14)); // 철근부식 면적율 셀
        }

        console.log(`손상물량 추출 완료:`, {crackData1d, crackData2d, leakData, surfaceData, rebarData});

        // 1방향 균열율 계산 및 업데이트
        if (crackData1d.hasData) {
            const newRatio = calculateCrackRatio(crackData1d.value, newArea);
            $cells.eq(4).text(newRatio > 0 ? newRatio.safeToFixed(2) : '-').attr('data-original-value', crackData1d.value);
            $cells.eq(5).text(evaluateGrade(newRatio, 'crack_ratio'));
            console.log(`1방향 균열율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }

        // 2방향 균열율 계산 및 업데이트
        if (crackData2d.hasData) {
            const newRatio = calculateAreaRatio(crackData2d.value, newArea);
            // $cells.eq(8).text(newRatio.safeToFixed(2)).attr('data-original-value', crackData2d.value);

            $cells.eq(8).text(newRatio > 0 ? newRatio.safeToFixed(2) : '-').attr('data-original-value', crackData2d.value);


            $cells.eq(9).text(evaluateGrade(newRatio, 'crack_ratio'));
            console.log(`2방향 균열율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }

        // 누수 면적율 계산 및 업데이트
        if (leakData.hasData) {
            const newRatio = calculateAreaRatio(leakData.value, newArea);
            //$cells.eq(10).text(newRatio.safeToFixed(2)).attr('data-original-value', leakData.value);

            calculateCurbArea($cells.eq(10), newRatio, leakData.value);

             $cells.eq(11).text(evaluateGrade(newRatio, 'leak_ratio'));
            console.log(`누수 면적율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }

        // 표면손상 면적율 계산 및 업데이트
        if (surfaceData.hasData) {
            const newRatio = calculateAreaRatio(surfaceData.value, newArea);
            calculateCurbArea($cells.eq(12), newRatio, surfaceData.value);
            $cells.eq(13).text(evaluateGrade(newRatio, 'surface_damage_ratio'));
            console.log(`표면손상 면적율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }

        // 철근부식 면적율 계산 및 업데이트
        if (rebarData.hasData) {
            const newRatio = calculateAreaRatio(rebarData.value, newArea);
            calculateCurbArea($cells.eq(14), newRatio, rebarData.value);
            $cells.eq(15).text(evaluateGrade(newRatio, 'rebar_corrosion_ratio'));
            console.log(`철근부식 면적율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }
    }

    // 가로보 계산 업데이트
    function updateCrossbeamCalculations($row, $cells, newArea) {
        // 가로보 테이블 구조: 경간, 점검면적, 1방향균열폭, 등급, 1방향균열율, 등급, 2방향균열폭, 등급, 2방향균열율, 등급, 누수면적율, 등급, 표면손상면적율, 등급, 철근부식면적율, 등급, 최종등급

        // 각 데이터 셀에서 원본 손상물량 추출
        const crackData1d = extractOriginalDamageValue($cells.eq(4)); // 1방향 균열율 셀
        const crackData2d = extractOriginalDamageValue($cells.eq(8)); // 2방향 균열율 셀
        const leakData = extractOriginalDamageValue($cells.eq(10)); // 누수 면적율 셀
        const surfaceData = extractOriginalDamageValue($cells.eq(12)); // 표면손상 면적율 셀
        const rebarData = extractOriginalDamageValue($cells.eq(14)); // 철근부식 면적율 셀

        console.log(`가로보 손상물량 추출:`, {crackData1d, crackData2d, leakData, surfaceData, rebarData});

        // 1방향 균열율 계산 및 업데이트
        if (crackData1d.hasData) {
            const newRatio = calculateCrackRatio(crackData1d.value, newArea);
            $cells.eq(4).text(newRatio > 0 ? newRatio.safeToFixed(2) : '-').attr('data-original-value', crackData1d.value);
            $cells.eq(5).text(evaluateGrade(newRatio, 'crack_ratio'));
            console.log(`가로보 1방향 균열율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }

        // 2방향 균열율 계산 및 업데이트
        if (crackData2d.hasData) {
            const newRatio = calculateAreaRatio(crackData2d.value, newArea);
            $cells.eq(8).text(newRatio > 0 ? newRatio.safeToFixed(2) : '-').attr('data-original-value', crackData2d.value);
            $cells.eq(9).text(evaluateGrade(newRatio, 'crack_ratio'));
            console.log(`가로보 2방향 균열율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }

        // 누수 면적율 계산 및 업데이트
        if (leakData.hasData) {
            const newRatio = calculateAreaRatio(leakData.value, newArea);
            calculateCurbArea($cells.eq(10), newRatio, leakData.value);


            $cells.eq(11).text(evaluateGrade(newRatio, 'leak_ratio'));
            console.log(`가로보 누수 면적율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }

        // 표면손상 면적율 계산 및 업데이트
        if (surfaceData.hasData) {
            const newRatio = calculateAreaRatio(surfaceData.value, newArea);
            calculateCurbArea($cells.eq(12), newRatio, surfaceData.value);


            $cells.eq(13).text(evaluateGrade(newRatio, 'surface_damage_ratio'));
            console.log(`가로보 표면손상 면적율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }

        // 철근부식 면적율 계산 및 업데이트
        if (rebarData.hasData) {
            const newRatio = calculateAreaRatio(rebarData.value, newArea);
            calculateCurbArea($cells.eq(14), newRatio, rebarData.value);

            $cells.eq(15).text(evaluateGrade(newRatio, 'rebar_corrosion_ratio'));
            console.log(`가로보 철근부식 면적율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }
    }

    // 교대 계산 업데이트
    function updateAbutmentCalculations($row, $cells, newArea) {
        // 교대 테이블 구조: 경간, 점검면적, 균열최대폭, 등급, 변위, 등급, 표면손상면적율, 등급, 철근부식면적율, 등급, 최종등급

        const surfaceData = extractOriginalDamageValue($cells.eq(6)); // 표면손상 면적율 셀
        const rebarData = extractOriginalDamageValue($cells.eq(8)); // 철근부식 면적율 셀

        console.log(`교대 손상물량 추출:`, {surfaceData, rebarData});

        // 표면손상 면적율 계산 및 업데이트
        if (surfaceData.hasData) {
            const newRatio = calculateAreaRatio(surfaceData.value, newArea);
            calculateCurbArea($cells.eq(6), newRatio, surfaceData.value);
            $cells.eq(7).text(evaluateGrade(newRatio, 'surface_damage_ratio'));
            console.log(`교대 표면손상 면적율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }

        // 철근부식 면적율 계산 및 업데이트
        if (rebarData.hasData) {
            const newRatio = calculateAreaRatio(rebarData.value, newArea);
            calculateCurbArea($cells.eq(8), newRatio, rebarData.value);
            $cells.eq(9).text(evaluateGrade(newRatio, 'rebar_corrosion_ratio'));
            console.log(`교대 철근부식 면적율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }
    }

    // 교각 계산 업데이트 (교대와 동일한 구조)
    function updatePierCalculations($row, $cells, newArea) {
        // 교각 테이블 구조: 경간, 점검면적, 균열최대폭, 등급, 변위, 등급, 표면손상면적율, 등급, 철근부식면적율, 등급, 최종등급

        const surfaceData = extractOriginalDamageValue($cells.eq(6)); // 표면손상 면적율 셀
        const rebarData = extractOriginalDamageValue($cells.eq(8)); // 철근부식 면적율 셀

        console.log(`교각 손상물량 추출:`, {surfaceData, rebarData});

        // 표면손상 면적율 계산 및 업데이트
        if (surfaceData.hasData) {
            const newRatio = calculateAreaRatio(surfaceData.value, newArea);
            calculateCurbArea($cells.eq(6), newRatio, surfaceData.value);
            $cells.eq(7).text(evaluateGrade(newRatio, 'surface_damage_ratio'));
            console.log(`교각 표면손상 면적율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }

        // 철근부식 면적율 계산 및 업데이트
        if (rebarData.hasData) {
            const newRatio = calculateAreaRatio(rebarData.value, newArea);
            calculateCurbArea($cells.eq(8), newRatio, rebarData.value);
            $cells.eq(9).text(evaluateGrade(newRatio, 'rebar_corrosion_ratio'));
            console.log(`교각 철근부식 면적율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }
    }

    // 포장 계산 업데이트
    function updatePavementCalculations($row, $cells, newArea) {
        // 포장 테이블 구조: 경간, 부재면적, 포장불량면적율, 등급, 주행성, 등급, 배수구막힘, 배수, 최종등급

        const damageData = extractOriginalDamageValue($cells.eq(2)); // 포장불량 면적율 셀

        console.log(`포장 손상물량 추출:`, {damageData});

        // 포장 타입에 따른 등급 평가 함수 선택
        const pavementType = $("#pavementType").val();
        const damageType = pavementType === 'CONCRETE' ? 'damage_ratio_concrete' : 'damage_ratio_asphalt';

        // 포장불량 면적율 계산 및 업데이트
        if (damageData.hasData) {
            const newRatio = calculateAreaRatio(damageData.value, newArea);
            //$cells.eq(2).text(newRatio > 0 ? newRatio.safeToFixed(2) : '-').attr('data-original-value', damageData.value);
            calculateCurbArea($cells.eq(2), newRatio, damageData.value);

            $cells.eq(3).text(evaluateGrade(newRatio, damageType));
            console.log(`포장불량 면적율 업데이트: ${newRatio > 0 ? newRatio.safeToFixed(2) : '-'}%`);
        }

        // 배수시설 데이터 확인 및 등급 적용
        const spanId = $cells.eq(0).text().trim(); // 경간 ID 추출
       // updatePavementDrainageGrade($row, $cells, spanId);
    }

    // 무한루프 방지 플래그
    let isUpdatingPavementDrainage = false;
    // 디바운싱을 위한 타이머
    let drainageUpdateTimeout = null;

    // // 포장 테이블의 배수 등급 업데이트 함수
    // function updatePavementDrainageGrade($row, $cells, spanId) {
    //     // 무한루프 방지
    //     if (isUpdatingPavementDrainage) {
    //         console.log('배수 등급 업데이트 중복 호출 방지');
    //         return;
    //     }

    //     // 배수시설 테이블에서 해당 경간의 손상 데이터 찾기
    //     const drainageTable = document.getElementById('drainageEvaluationTable');
    //     if (!drainageTable) {
    //         console.log('배수시설 테이블을 찾을 수 없습니다.');
    //         return;
    //     }

    //     // 해당 경간의 배수시설 데이터 찾기
    //     const drainageRows = drainageTable.querySelectorAll('tbody tr');
    //     let drainageGrade = 'a'; // 기본값
    //     let damageStatus = '양호'; // 기본값

    //     // for (let row of drainageRows) {
    //     //     const rowSpanId = row.cells[0].textContent.trim();
    //     //     if (rowSpanId === spanId) {
    //     //         damageStatus = row.cells[1].textContent.trim();
    //     //         drainageGrade = row.cells[2].textContent.trim();
    //     //         break;
    //     //     }
    //     // }

    //     // 배수구 막힘만 처리 (b등급 적용)
    //     if (damageStatus.includes('배수구 막힘') || damageStatus.includes('막힘')) {
    //         // 교면포장 배수 평가 적용 (배수구 막힘은 b등급)
    //         if (typeof evaluatePavementDrainage === 'function') {
    //             drainageGrade = evaluatePavementDrainage(damageStatus);
    //         } else {
    //             drainageGrade = 'b'; // 기본적으로 배수구 막힘은 b등급
    //         }

    //         // 포장 테이블의 배수 열 업데이트 (6번째와 7번째 셀)
    //         $cells.eq(6).text(damageStatus);
    //         $cells.eq(7).text(drainageGrade);

    //         console.log(`포장 ${spanId} 배수구 막힘 등급 업데이트: ${damageStatus} -> ${drainageGrade}`);
    //     } else {
    //         console.log(`포장 ${spanId} 배수구 막힘이 아니므로 처리하지 않음: ${damageStatus}`);
    //         return; // 배수구 막힘이 아니면 처리하지 않음
    //     }

    //     // 최종 등급 재계산 (무한루프 방지 플래그 설정)
    //     isUpdatingPavementDrainage = true;
    //     updateFinalGrade($row);
    //     isUpdatingPavementDrainage = false;
    // }

    // 배수시설 테이블에서 포장 테이블의 배수 등급 일괄 업데이트
    function updatePavementDrainageFromDrainageTable() {
        // 무한루프 방지
        if (isUpdatingPavementDrainage) {
            console.log('배수 테이블 일괄 업데이트 중복 호출 방지');
            return;
        }

        console.log('배수시설 테이블에서 포장 테이블 배수 등급 업데이트 시작');

        // 무한루프 방지 플래그 설정
        isUpdatingPavementDrainage = true;

        const pavementTable = document.getElementById('pavementEvaluationTable');
        if (!pavementTable) {
            console.log('포장 테이블을 찾을 수 없습니다.');
            return;
        }

        const drainageTable = document.getElementById('drainageEvaluationTable');
        if (!drainageTable) {
            console.log('배수시설 테이블을 찾을 수 없습니다.');
            return;
        }

        // 포장 테이블의 모든 행 처리
        const pavementRows = pavementTable.querySelectorAll('tbody tr');
        pavementRows.forEach(row => {
            const cells = row.cells;
            const spanId = cells[0].textContent.trim();

            // 배수시설 테이블에서 해당 경간의 데이터 찾기
            const drainageRows = drainageTable.querySelectorAll('tbody tr');
            let drainageGrade = 'a';
            let damageStatus = '양호';

            for (let drainageRow of drainageRows) {
                const drainageSpanId = drainageRow.cells[0].textContent.trim();
                if (drainageSpanId === spanId) {
                    const damageText = drainageRow.cells[1].textContent.replace(/\s+/g, ''); // 공백 제거
                    var drainData = ['배수구막힘','배수관막힘','배수구퇴적','퇴적'];
                    for(let data of drainData) {
                        if(damageText.includes(data)) {
                            damageStatus = data;
                            drainageGrade = "b";
                            break; // 첫 번째 매칭되는 항목에서 중단
                        }
                    }
                }
            }

            // 교면포장 배수 평가 적용
            if (typeof evaluatePavementDrainage === 'function') {
                drainageGrade = evaluatePavementDrainage(damageStatus);
            }

            // 포장 테이블의 배수 열 업데이트 (6번째와 7번째 셀)
            if (cells.length > 7) {

                cells[6].textContent = damageStatus;
                cells[7].textContent = drainageGrade;

                // 최종 등급 재계산
                const $row = $(row);
                updateFinalGrade($row);

                console.log(`포장 ${spanId} 배수 등급 업데이트: ${damageStatus} -> ${drainageGrade}`);
            }
        });

        console.log('포장 테이블 배수 등급 업데이트 완료');

        // 무한루프 방지 플래그 해제
        isUpdatingPavementDrainage = false;
    }

    // 난간 및 연석 계산 업데이트
    function updateRailingCalculations($row, $cells, newArea) {
        // 난간 테이블 구조: 구분, 길이, 도장손상(%), 등급, 부식발생(%), 등급, 연결재및단면손상(%), 등급, 균열최대폭(mm), 등급, 표면손상면적율(%), 등급, 철근부식손상면적율(%), 등급, 상태평가결과

        const paintDamageData = extractOriginalDamageValue($cells.eq(2)); // 도장손상 셀
        const corrosionData = extractOriginalDamageValue($cells.eq(4)); // 부식발생 셀
        const damageRatioData = extractOriginalDamageValue($cells.eq(6)); // 연결재및단면손상 셀
        const crackWidthData = extractOriginalDamageValue($cells.eq(8)); // *** 균열최대폭 셀 추가 ***
        const surfaceData = extractOriginalDamageValue($cells.eq(10)); // 표면손상 셀
        const rebarData = extractOriginalDamageValue($cells.eq(12)); // 철근부식 셀

        console.log(`난간 손상물량 추출:`, {paintDamageData, corrosionData, damageRatioData, surfaceData, rebarData});

        // 도장손상 면적율 계산 및 업데이트
        if (paintDamageData.hasData) {
            const newRatio = calculateAreaRatio(paintDamageData.value, newArea);
            $cells.eq(2).text(newRatio > 0 ? newRatio.safeToFixed(2) : '-').attr('data-original-value', paintDamageData.value);
            calculateCurbArea($cells.eq(2), newRatio, paintDamageData.value);
            $cells.eq(3).text(evaluateGrade(newRatio, 'paint_damage_ratio'));
            console.log(`난간 도장손상 면적율 업데이트: ${newRatio > 0 ? newRatio.safeToFixed(2) : '-'}%`);
        }

        // 부식발생 면적율 계산 및 업데이트
        if (corrosionData.hasData) {
            const newRatio = calculateAreaRatio(corrosionData.value, newArea);
            //$cells.eq(4).text(newRatio > 0 ? newRatio.safeToFixed(2) : '-').attr('data-original-value', corrosionData.value);
            calculateCurbArea($cells.eq(4), newRatio, corrosionData.value);

            $cells.eq(5).text(evaluateGrade(newRatio, 'sub_rust_area'));
            console.log(`난간 부식발생 면적율 업데이트: ${newRatio > 0 ? newRatio.safeToFixed(2) : '-'}%`);
        }

        // 연결재 및 단면손상 면적율 계산 및 업데이트
        if (damageRatioData.hasData) {
            const newRatio = calculateAreaRatio(damageRatioData.value, newArea);
            //$cells.eq(6).text(newRatio > 0 ? newRatio.safeToFixed(2) : '-').attr('data-original-value', damageRatioData.value);
            calculateCurbArea($cells.eq(6), newRatio, damageRatioData.value);
            $cells.eq(7).text(evaluateGrade(newRatio, 'section_loss_ratio'));
            console.log(`난간 연결재및단면손상 면적율 업데이트: ${newRatio > 0 ? newRatio.safeToFixed(2) : '-'}%`);
        }

        // *** 균열 최대폭 처리 추가 ***
        if (crackWidthData.hasData) {
        // 균열폭은 면적과 무관하므로 원본 값 그대로 사용
            $cells.eq(8).text(crackWidthData.value > 0 ? crackWidthData.value.safeToFixed(2) : '-').attr('data-original-value', crackWidthData.value);
            calculateCurbArea($cells.eq(8), newRatio, crackWidthData.value);

            $cells.eq(9).text(evaluateGrade(crackWidthData.value, 'crack_width'));
            console.log(`난간 균열 최대폭 업데이트: ${crackWidthData.value > 0 ? crackWidthData.value.safeToFixed(2) : '-'}mm`);
    }
        // 표면손상 면적율 계산 및 업데이트
        if (surfaceData.hasData) {
            const newRatio = calculateAreaRatio(surfaceData.value, newArea);
            //$cells.eq(10).text(newRatio > 0 ? newRatio.safeToFixed(2) : '-').attr('data-original-value', surfaceData.value);
            calculateCurbArea($cells.eq(10), newRatio, surfaceData.value);

            $cells.eq(11).text(evaluateGrade(newRatio, 'surface_damage_ratio'));
            console.log(`난간 표면손상 면적율 업데이트: ${newRatio > 0 ? newRatio.safeToFixed(2) : '-'}%`);
        }

        // 철근부식 손상면적율 계산 및 업데이트
        if (rebarData.hasData) {
            const newRatio = calculateAreaRatio(rebarData.value, newArea);
            //$cells.eq(12).text(newRatio > 0 ? newRatio.safeToFixed(2) : '-').attr('data-original-value', rebarData.value);
            calculateCurbArea($cells.eq(12), newRatio, rebarData.value);
            $cells.eq(13).text(evaluateGrade(newRatio, 'rebar_corrosion_ratio'));
            console.log(`난간 철근부식 손상면적율 업데이트: ${newRatio > 0 ? newRatio.safeToFixed(2) : '-'}%`);
        }
    }

    // 원본 손상물량 값 추출
    function extractOriginalDamageValue($cell) {
        // 이미 data-original-value가 있으면 사용
        const originalValue = $cell.attr('data-original-value');
        if (originalValue !== undefined) {
            const value = parseFloat(originalValue);
            return { hasData: !isNaN(value) && value > 0, value: value || 0 };
        }

        // 셀의 현재 텍스트에서 숫자 추출
        const cellText = $cell.text().trim();
        if (cellText === '-' || cellText === '') {
            return { hasData: false, value: 0 };
        }

        const value = parseFloat(cellText);
        if (!isNaN(value) && value > 0) {
            // 처음 추출한 값을 data-original-value로 저장
            $cell.attr('data-original-value', value);
            return { hasData: true, value: value };
        }

        return { hasData: false, value: 0 };
    }

    // 균열율 계산 (입력값 * 0.25 / 점검면적 * 100)
    function calculateCrackRatio(damageQuantity, inspectionArea) {
        if (inspectionArea <= 0) return 0;
        return damageQuantity ? ((damageQuantity * 0.25 / inspectionArea) * 100) : 0;
    }

    // 면적율 계산 (입력값 / 점검면적 * 100)
    function calculateAreaRatio(damageQuantity, inspectionArea) {
        if (inspectionArea <= 0) return 0;
         const value = damageQuantity? ((damageQuantity / inspectionArea) * 100) : 0.00;

        if(damageQuantity>0 && value < 0.01) {
            return 0.01;
        }

        return value.safeToFixed(2);
    }

    // 해당 경간의 가장 낮은 등급(가장 심각한 등급) 계산
    function calculateWorstGrade(...gradeValues) {
        console.log('calculateWorstGrade 호출, 입력 등급들:', gradeValues);

        const validGrades = [];

        // 각 등급 값을 처리하여 유효한 등급만 수집
        gradeValues.forEach(gradeValue => {
            if (gradeValue === null || gradeValue === undefined || gradeValue === '-' || gradeValue === 0 || gradeValue === '0') {
                // 손상이 없는 경우 'a' 등급
                validGrades.push('a');
            } else if (typeof gradeValue === 'string' && ['a', 'b', 'c', 'd', 'e'].includes(gradeValue.toLowerCase())) {
                // 이미 등급인 경우
                validGrades.push(gradeValue.toLowerCase());
            } else {
                // 숫자값인 경우 evaluateGrade 함수를 통해 등급 계산
                const grade = evaluateGrade(gradeValue);
                validGrades.push(grade);
            }
        });

        console.log('유효한 등급들:', validGrades);

        // 가장 심각한 등급 찾기 (e > d > c > b > a 순서)
        const gradeOrder = ['a', 'b', 'c', 'd', 'e'];
        let worstGrade = 'a';

        validGrades.forEach(grade => {
            if (gradeOrder.indexOf(grade) > gradeOrder.indexOf(worstGrade)) {
                worstGrade = grade;
            }
        });

        console.log('최종 선택된 가장 심각한 등급:', worstGrade);
        return worstGrade;
    }

    // 최종 등급 업데이트 (기존 로직 유지)
    function updateFinalGrade($row) {
        const grades = [];
        $row.find('td').each(function() {
            const text = $(this).text().trim();
            if (['a', 'b', 'c', 'd', 'e'].includes(text)) {
                grades.push(text);
            }
        });

        // 가장 심각한 등급 선택 (calculateWorstGrade 사용)
        const finalGrade = calculateWorstGrade(...grades);

        $row.find('td:last strong').text(finalGrade);
        console.log('updateFinalGrade 결과:', finalGrade);

        // 통합 상태평가 자동 업데이트
        updateTotalEvaluationTableIfVisible();
    }

    // 손상 데이터 생성에 필요한 보조 함수들
    function getRandomDamageValue(min, max) {
        return (Math.random() * (max - min) + min).safeToFixed(2);
    }

    function getRandomDeformation() {
        const deformations = ['-', '소요', '중요', '심각'];
        return deformations[Math.floor(Math.random() * deformations.length)];
    }

    function getRandomDamageCondition() {
        const conditions = ['-', '소요', '중요', '심각'];
        return conditions[Math.floor(Math.random() * conditions.length)];
    }

    function getRandomErosionCondition() {
        const conditions = ['-', '상부노출', '중요', '심각'];
        return conditions[Math.floor(Math.random() * conditions.length)];
    }

    function getRandomSettlementCondition() {
        const conditions = ['-', '상부노출', '중요', '심각'];
        return conditions[Math.floor(Math.random() * conditions.length)];
    }

    function getRandomBearingCondition() {
        const conditions = ['-', '본체 부식', '노화', '파손'];
        return conditions[Math.floor(Math.random() * conditions.length)];
    }

    function getRandomExpansionJointCondition() {
        const conditions = ['-', '본체 부식', '노화', '파손'];
        return conditions[Math.floor(Math.random() * conditions.length)];
    }

    function getRandomDamagePercentage() {
        const percentages = ['양호', '소요', '중요', '심각'];
        return percentages[Math.floor(Math.random() * percentages.length)];
    }

    function getRandomTrafficGrade() {
        const grades = ['양호', '소요', '중요', '심각'];
        return grades[Math.floor(Math.random() * grades.length)];
    }

    function getRandomDrainageCondition() {
        const conditions = ['양호', '토사퇴적', '파손', '누수'];
        return conditions[Math.floor(Math.random() * conditions.length)];
    }


    // 상태평가 생성 함수 수정 (경간 피벗)
    function generateEvaluationTable(componentType, data) {
        const tableElement = document.getElementById(`${componentType}EvaluationTable`);
        if (!tableElement) return;

        console.log(`${componentType} 상태평가 생성 시작, 데이터:`, data);

        // API 데이터를 전역에 저장하여 updateSlabGirderCalculations에서 접근 가능하도록 함
        window.currentEvaluationData = data;

        let tableHtml = '';
        // 부재별 테이블 헤더 생성
        switch(componentType) {
            case 'slab':
                let slabtype = $("#slabType").val();
                tableHtml = generateSlabTableHeader(slabtype);
                break;
            case 'girder':
                tableHtml = generateGirderTableHeader();
                break;
            case 'crossbeam':
                tableHtml = generateCrossbeamTableHeader();
                break;
            case 'abutment':
                tableHtml = generateAbutmentTableHeader();
                break;
            case 'pier':
                tableHtml = generatePierTableHeader();
                break;
            case 'foundation':
                tableHtml = generateFoundationTableHeader();
                break;
            case 'bearing':
                tableHtml = generateBearingTableHeader();
                break;
            case 'expansionJoint':
                tableHtml = generateExpansionJointTableHeader();
                break;
            case 'pavement':
                tableHtml = generatePavementTableHeader();
                break;
            case 'drainage':
                tableHtml = generateDrainageTableHeader();
                break;
            case 'railing':
                tableHtml = generateRailingTableHeader();
                break;
        }

        tableHtml += '<tbody>';

        // Helper function: 각 경간별로 inspectionArea 가져오기
        function getInspectionAreaForSpan(spanId, componentType) {
            //alert("spanId="+spanId+"//"+componentType);
            if (Array.isArray(get_span_damage) && get_span_damage.length > 0) {
                const matchingDamage = get_span_damage.find(
                    d => d.spanId === spanId && d.type === componentType && d.inspectionArea
                );
                if (matchingDamage && matchingDamage.inspectionArea) {
                    return parseFloat(matchingDamage.inspectionArea) || 100;
                }
            }
            return 100; // 기본값
        }

        // 신축이음의 경우 별도 처리
        if (componentType === 'expansionJoint') {
            console.log('신축이음 별도 처리 시작');

            // 사용자가 입력한 신축이음 위치 정보를 활용
            const expansionPositions = $('#expansionJointPositions').val();
            let expansionLocations = [];

            if (expansionPositions && expansionPositions.trim()) {
                // 사용자가 입력한 신축이음 위치만 표시
                expansionLocations = expansionPositions.split(',').map(loc => loc.trim().toUpperCase()).filter(loc => loc);
            } else {
                // 입력이 없으면 기존 bridgeData.expansionJointLocations 사용
                expansionLocations = bridgeData.expansionJointLocations ?
                    bridgeData.expansionJointLocations.split(',').map(loc => loc.trim()).filter(loc => loc) : [];
            }

            console.log('파싱된 신축이음 위치 배열:', expansionLocations);

            if (expansionLocations.length > 0) {
                // 설정된 신축이음 위치에 따라 행 생성
                expansionLocations.forEach(locationData => {
                    console.log(`신축이음 위치 ${locationData}에 대한 행 생성`);


                    // 해당 위치의 실제 데이터 검색
                    const spanDamageData = data.filter ? data.filter(d => d.span_id === locationData) : [];

                    if (spanDamageData.length > 0) {
                        console.log(`실제 데이터 있음: ${locationData}`, spanDamageData[0]);
                        tableHtml += generateTableRowFromData(componentType, locationData, spanDamageData[0], getInspectionAreaForSpan(locationData, componentType));
                    } else {
                        console.log(`실제 데이터 없음, 빈 행 생성: ${locationData}`);
                        tableHtml += generateEmptyTableRow(componentType, locationData, getInspectionAreaForSpan(locationData, componentType));
                    }
                });
            } else {
                // 신축이음 위치 정보가 없으면 기본값으로 A1, A2 생성
                console.log('신축이음 위치 정보 없음, 기본 A1, A2 행 생성');
                const defaultExpansionLocations = ['A1', 'A2'];

                defaultExpansionLocations.forEach(locationData => {
                    console.log(`기본 신축이음 위치 ${locationData}에 대한 행 생성`);

                    // 해당 위치의 실제 데이터 검색
                    const spanDamageData = data.filter ? data.filter(d => d.span_id === locationData) : [];

                    if (spanDamageData.length > 0) {
                        console.log(`실제 데이터 있음: ${locationData}`, spanDamageData[0]);
                        tableHtml += generateTableRowFromData(componentType, locationData, spanDamageData[0], getInspectionAreaForSpan(locationData, componentType));
                    } else {
                        console.log(`실제 데이터 없음, 빈 행 생성: ${locationData}`);
                        tableHtml += generateEmptyTableRow(componentType, locationData, getInspectionAreaForSpan(locationData, componentType));
                    }
                });
            }
        }
        // 다른 부재들은 bridgeData.spans를 기준으로 처리
        else if (bridgeData.spans && bridgeData.spans.length > 0) {
            bridgeData.spans.forEach(span => {
                // 해당 부재에 맞는 경간만 출력
                let valid = false;
                if (componentType === 'bearing') {
                    valid = span.id.startsWith('A') || span.id.startsWith('P');
                } else if (componentType === 'slab' || componentType === 'girder' || componentType === 'crossbeam' || componentType === 'pavement' || componentType === 'drainage' || componentType === 'railing') {
                    valid = span.id.startsWith('S');
                } else if (componentType === 'abutment') {
                    valid = span.id.startsWith('A');
                } else if (componentType === 'pier') {
                    valid = span.id.startsWith('P');
                } else if (componentType === 'foundation') {
                    // 기초는 노출된 기초 위치 정보를 활용
                    const exposedPositions = $('#exposedFoundationPositions').val();
                    if (exposedPositions && exposedPositions.trim()) {
                        const exposedArray = exposedPositions.split(',').map(pos => pos.trim().toUpperCase());
                        valid = exposedArray.includes(span.id.toUpperCase());
                    } else {
                        valid = span.id.startsWith('A') || span.id.startsWith('P');
                    }
                }

                if (!valid) return;

                // 해당 경간의 손상 데이터 수집
                const spanDamageData = data.filter ? data.filter(d => d.span_id === span.id) : [];

                if (spanDamageData.length > 0) {
                    // 실제 데이터를 기반으로 테이블 행 생성
                    // 수정이 필요한 부분
                    tableHtml += generateTableRowFromData(componentType, span.id, spanDamageData[0], getInspectionAreaForSpan(span.id, componentType));
                } else if (componentType === 'foundation') {
                    // 노출된 기초이지만 손상 데이터가 없는 경우: "기초 노출" 표시 및 b등급
                    tableHtml += `
                        <tr>
                                    <td>${span.id}</td>
                                    <td>-</td><td>a</td>
                                    <td>-</td><td>a</td>
                                    <td>기초 노출</td><td>b</td>
                                    <td>-</td><td>a</td>
                                    <td><strong>b</strong></td>
                        </tr>
                    `;
                } else {
                    // 데이터가 없으면 기본값으로 표시
                    tableHtml += generateEmptyTableRow(componentType, span.id, getInspectionAreaForSpan(span.id, componentType));
                }
            });
        } else {
            // spans 데이터가 없으면 기본 경간 생성
            const defaultSpans = componentType === 'expansionJoint' ? ['A1', 'A2'] : ['S1', 'S2', 'S3'];
            defaultSpans.forEach(spanId => {

                const spanDamageData = data.filter ? data.filter(d => d.span_id === spanId) : [];
                if (spanDamageData.length > 0) {
                    tableHtml += generateTableRowFromData(componentType, c, spanDamageData[0], getInspectionAreaForSpan(spanId, componentType));
                } else {
                    tableHtml += generateEmptyTableRow(componentType, spanId, getInspectionAreaForSpan(spanId, componentType));
                }
            });
        }

        tableHtml += '</tbody>';
        tableElement.innerHTML = tableHtml;

        // 배수시설 테이블이 생성된 후 포장 테이블의 배수 등급 업데이트
        if (componentType === 'drainage') {
            updatePavementDrainageFromDrainageTable();
        }

        console.log(`${componentType} 상태평가 생성 완료`);
    }


    // 빈 테이블 행 생성
    function generateEmptyTableRow(componentType, spanId, inspectionArea) {
        let emptyRow = `<tr><td>${spanId}</td>`;

        switch(componentType) {
            case 'slab':
                // 바닥판 타입 확인 (강바닥판인지 일반 바닥판인지)
                const slabType = $("#slabType").val();
                if (slabType === 'STEEL') {
                    // 강바닥판 구조: 경간, 점검면적, 부재균열, 등급, 변형파단, 등급, 연결볼트이완탈락, 등급, 용접연결부결함, 등급, 표면열화면적율, 등급, 최종등급
                    emptyRow += `<td><input type="number" class="form-control area-input" value="${inspectionArea}" step="0.1"></td>`;
                    emptyRow += '<td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                } else {
                    // 일반 바닥판 구조
                    emptyRow += `<td><input type="number" class="form-control area-input" value="${inspectionArea}" step="0.1"></td>`;
                    emptyRow += '<td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                }
                break;
            case 'girder':
                const girderType = $("#girderType").val();
                if (girderType === 'STEEL') {
                    emptyRow += `<td><input type=\"number\" class=\"form-control area-input\" value=\"${inspectionArea}\" step=\"0.1\"></td>`;
                    emptyRow += '<td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                } else {
                    emptyRow += `<td><input type=\"number\" class=\"form-control area-input\" value=\"${inspectionArea}\" step=\"0.1\"></td>`;
                    emptyRow += '<td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                }
                break;
            case 'crossbeam':
                const crossbeamType = $("#crossbeamType").val();
                if (crossbeamType === 'STEEL') {
                    emptyRow += `<td><input type=\"number\" class=\"form-control area-input\" value=\"${inspectionArea}\" step=\"0.1\"></td>`;
                    emptyRow += '<td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                } else {
                    emptyRow += `<td><input type=\"number\" class=\"form-control area-input\" value=\"${inspectionArea}\" step=\"0.1\"></td>`;
                    emptyRow += '<td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                }
                break;
            case 'abutment':
                emptyRow += `<td><input type="number" class="form-control area-input" value="${inspectionArea}" step="0.1"></td>`;
                emptyRow += '<td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                break;
            case 'pier':
                emptyRow += `<td><input type="number" class="form-control area-input" value="${inspectionArea}" step="0.1"></td>`;
                emptyRow += '<td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                break;
            case 'foundation':
                emptyRow += '<td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                break;
            case 'bearing':
                emptyRow += '<td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                break;
            case 'expansionJoint':
                emptyRow += '<td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                break;
            case 'pavement':
                emptyRow += `<td><input type="number" class="form-control area-input" value="${inspectionArea}" step="0.1"></td>`;
                emptyRow += '<td>-</td><td>a</td><td>양호</td><td>a</td><td>양호</td><td>a</td><td><strong>a</strong></td>';
                break;
            case 'drainage':
                emptyRow += '<td>-</td><td><strong>a</strong></td>';
                break;
            case 'railing':
                emptyRow += `<td><input type="number" class="form-control area-input" value="${inspectionArea}" step="0.1"></td>`;
                emptyRow += `<td>-</td>`;
                emptyRow += `<td>a</td>`;
                emptyRow += `<td>-</td>`;
                emptyRow += `<td>a</td>`;
                emptyRow += `<td>-</td>`;
                emptyRow += `<td>a</td>`;
                emptyRow += `<td>-</td>`;
                emptyRow += `<td>a</td>`;
                emptyRow += `<td>-</td>`;
                emptyRow += `<td>a</td>`;
                emptyRow += `<td>a</td>`;
                // 2025/7/22 spark 수정
                //emptyRow +=  `<td>a</td>`;
                //emptyRow +=  `<td>-</td>`;
                //emptyRow +=  `<td>a</td>`;
                //emptyRow +=  `<td><strong>a</strong></td>`;
                break;
        }
        emptyRow += '</tr>';
        return emptyRow;
    }

    // 부재별 테이블 헤더 생성 함수들
    function generateSlabTableHeader(type) {
        // type이 'STEEL'이면 강바닥판/강거더 구조, 아니면 콘크리트 구조
        if (type === 'STEEL') {
            return `  <thead class="table-dark">
                <tr>
                    <th rowspan="2">구 분</th>
                    <th rowspan="2">점검<br>면적<br>(m²)</th>
                    <th colspan="8">모재 및 연결부 손상</th>
                    <th colspan="2" rowspan="2">표면열화<br>면적율(%)</th>
                    <th rowspan="2">상태<br>평가<br>결과</th>
                </tr>
                <tr>
                    <th colspan="2">부재 균열</th>
                    <th colspan="2">변형, 파단</th>
                    <th colspan="2">연결 볼트<br>이완, 탈락</th>
                    <th colspan="2">용접연결부<br>결함</th>
                </tr>
            </thead>`;
        } else {
            return `
                <thead>
                    <tr>
                        <th rowspan="2">구 분</th>
                        <th rowspan="2">점검<br>면적<br>(m²)</th>
                        <th colspan="4">1방향 균열</th>
                        <th colspan="4">2방향 균열</th>
                        <th colspan="6">열화 및 손상</th>
                        <th rowspan="2">상태<br>평가<br>결과</th>
                    </tr>
                    <tr>
                        <th colspan="2">최대폭(mm)</th><th colspan="2">균열율(%)</th>
                        <th colspan="2">최대폭(mm)</th><th colspan="2">균열율(%)</th>
                        <th colspan="2">누수 및 백태<br>면적율(%)</th>
                        <th colspan="2">표면손상<br>면적율(%)</th>
                        <th colspan="2">철근부식<br>손상면적율(%)</th>
                    </tr>
                </thead>
            `;
        }
    }

    function generateGirderTableHeader() {
        const girderType = $("#girderType").val();
        if (girderType === 'STEEL') {
            return generateSlabTableHeader('STEEL'); // slabType과 무관하게 강거더 구조
        }
        return generateSlabTableHeader('CONCRETE'); // 콘크리트 거더 구조
    }

    function generateCrossbeamTableHeader() {
        const crossbeamType = $("#crossbeamType").val();
        if (crossbeamType === 'STEEL') {
            // 표 1.17 구조
            return `
                <thead>
                    <tr>
                        <th rowspan="2">구 분</th>
                        <th rowspan="2">점검<br>면적<br>(m²)</th>
                        <th colspan="8">모재 및 연결부 손상</th>
                        <th colspan="2" rowspan="2">표면열화<br>면적율(%)</th>
                        <th rowspan="2">상태<br>평가<br>결과</th>
                    </tr>
                    <tr>
                        <th colspan="2">부재 균열</th>
                        <th colspan="2">변형, 파단</th>
                        <th colspan="2">연결 볼트<br>이완, 탈락</th>
                        <th colspan="2">용접연결부<br>결함</th>
                    </tr>
                </thead>
            `;
        }
        // ... 기존 콘크리트 가로보 헤더
        return `
            <thead>
                <tr>
                    <th rowspan="2">구 분</th>
                    <th rowspan="2">점검<br>면적<br>(m²)</th>
                    <th colspan="4">1방향 균열</th>
                    <th colspan="4">2방향 균열</th>
                    <th colspan="6">열화 및 손상</th>
                    <th rowspan="2">상태<br>평가<br>결과</th>
                </tr>
                <tr>
                    <th colspan="2">최대폭(mm)</th><th colspan="2">균열율(%)</th>
                    <th colspan="2">최대폭(mm)</th><th colspan="2">균열율(%)</th>
                    <th colspan="2">누수 및 백태<br>면적율(%)</th>
                    <th colspan="2">표면손상<br>면적율(%)</th>
                    <th colspan="2">철근부식<br>손상면적율(%)</th>
                </tr>
            </thead>
        `;
    }

    function generateAbutmentTableHeader() {
        return `
            <thead>
                <tr>
                    <th rowspan="2">구 분</th>
                    <th rowspan="2">점검<br>면적<br>(m²)</th>
                    <th colspan="4">균열, 변위</th>
                    <th colspan="4">열화 및 손상</th>
                    <th rowspan="2">상태<br>평가<br>결과</th>
                </tr>
                <tr>
                    <th colspan="2">균열<br>최대폭(mm)</th>
                    <th colspan="2">변위</th>
                    <th colspan="2">표면손상<br>면적율(%)</th>
                    <th colspan="2">철근부식<br>손상면적율(%)</th>
                </tr>
            </thead>
        `;
    }

    // 기초 상태평가 테이블 헤더 (기존 교각 테이블)
    function generateFoundationTableHeader() {
        return `
            <thead>
                <tr>
                    <th rowspan="2">구 분</th>
                    <th colspan="4">기초(직접, 말뚝, 케이슨) 손상</th>
                    <th colspan="4">지반의 안정성</th>
                    <th rowspan="2">상태<br>평가<br>결과</th>
                </tr>
                <tr>
                    <th colspan="2">균열<br>최대폭(mm)</th>
                    <th colspan="2">단면손상</th>
                    <th colspan="2">세굴 여부</th>
                    <th colspan="2">침하(mm)</th>
                </tr>
            </thead>
        `;
    }

    // 교각 상태평가 테이블 헤더 (교대와 동일한 구조)
    function generatePierTableHeader() {
        return `
            <thead>
                <tr>
                    <th rowspan="2">구 분</th>
                    <th rowspan="2">점검<br>면적<br>(m²)</th>
                    <th colspan="4">균열, 변위</th>
                    <th colspan="4">열화 및 손상</th>
                    <th rowspan="2">상태<br>평가<br>결과</th>
                </tr>
                <tr>
                    <th colspan="2">균열<br>최대폭(mm)</th>
                    <th colspan="2">변위</th>
                    <th colspan="2">표면손상<br>면적율(%)</th>
                    <th colspan="2">철근부식<br>손상면적율(%)</th>
                </tr>
            </thead>
        `;
    }

    function generateBearingTableHeader() {
        return `
            <thead>
                <tr>
                    <th rowspan="2">구 분</th>
                    <th rowspan="2" colspan="2">받침본체(탄성받침, 강재받침)</th>
                    <th colspan="4">받침 콘크리트 등</th>
                    <th rowspan="2">상태평가 결과</th>
                </tr>
                <tr>
                    <th colspan="2">균열 최대폭(mm)</th>
                     <th colspan="2">단면손상</th>
                 </tr>
            </thead>
        `;
    }

    function generateExpansionJointTableHeader() {
        return `
            <thead>
                <tr>
                    <th colspan="1" rowspan="2">구 분</th>
                    <th colspan="2" rowspan="2">본체</th>
                    <th colspan="4">후타재</th>
                    <th rowspan="2">상태평가 결과</th>
                </tr>
                <tr>
                    <th colspan="2">균열</th>
                    <th colspan="2">단면손상</th>
                </tr>
            </thead>
        `;
    }

    function generatePavementTableHeader() {
        return `
            <thead>
                <tr>
                    <th rowspan="2">구분</th>
                    <th rowspan="2">부재면적<br>(m²)</th>
                    <th colspan="4">포장불량</th>
                    <th rowspan="2" colspan="2">배수</th>
                    <th rowspan="2">상태평가<br>결과</th>
                </tr>
                <tr>
                    <th colspan="2">포장불량<br>면적율(%)</th>
                    <th colspan="2">포장손상에<br>따른 주행성</th>
                </tr>
            </thead>
        `;
    }

    function generateDrainageTableHeader() {
        return `
            <thead>
                <tr>
                    <th rowspan="2">구 분</th>
                    <th>배수구/배수관</th>
                    <th rowspan="2">상태평가 결과</th>
                </tr>
                <tr>
                    <th>손상현황</th>
                </tr>
            </thead>
        `;
    }

    function generateRailingTableHeader() {
        return `
                <thead>
                    <tr>
                    <th rowspan="2">구 분</th>
                    <th rowspan="2">길이(m)</th>
                    <th colspan="6">강재</th>
                    <th colspan="4">콘크리트</th>
                    <th rowspan="2">상태평가 결과</th>
                    </tr>
                    <tr>
                    <th colspan="2">도장손상(%)</th>
                    <th colspan="2">부식발생(%)</th>
                    <th colspan="2">연결재 및 단면손상(%)</th>
                    <th colspan="2">균열 최대폭(mm)</th>
                    <th colspan="2">표면손상, 철근노출(%)</th>
                    </tr>
                </thead>
        `;
    }
    function isNumber(value) {
        if (typeof value === 'string') {
            // 따옴표 제거 및 숫자 변환
            value = parseFloat(value.replace(/"/g, ''));
        }

      return typeof value === 'number' && !isNaN(value);
    }
    // 서버 평가 데이터로부터 테이블 행 생성
    function generateTableRowFromData(componentType, spanId, data, inspectionArea) {
        // get_span_damage에서 해당 spanId의 inspectionArea 값을 우선 사용
        let area = inspectionArea;
        if (Array.isArray(get_span_damage)) {
            const found = get_span_damage.find(
                d => d.spanId === spanId && d.type === componentType
            );
            if (found && found.inspectionArea) {
                area = found.inspectionArea;
            }
        }
        let surface_damage_ratio_org = data.surface_damage_ratio;

        let surface_damage_ratio = data.surface_damage_ratio;


        // 문자열로 숫자가 들어오는 경우도 처리
        if (typeof surface_damage_ratio === 'string') {
            // 따옴표 제거 및 숫자 변환
            surface_damage_ratio = parseFloat(surface_damage_ratio.replace(/"/g, ''));
        }

        // 안전하게 숫자인지 확인 후 safeToFixed 사용
        if (isNumber(surface_damage_ratio)) {
            surface_damage_ratio = surface_damage_ratio.safeToFixed(2);
        } else {
            surface_damage_ratio = '-';
        }

        data.surface_damage_ratio = surface_damage_ratio;
        // 교량 정보 입력란에 값 설정

        crack_ratio_1d = data.crack_ratio_1d ;
        crack_ratio_2d = data.crack_ratio_2d ;

        // makeTwoLineValue 함수 추가
        function makeTwoLineValue(originalValue, calculatedValue) {
            if (typeof originalValue === 'number') {
                originalValue = originalValue.safeToFixed(2);
            }
            if (typeof calculatedValue === 'number') {
                calculatedValue = calculatedValue.safeToFixed(2);
            }

            // 원본값이 0이면 "-" 반환
            if (originalValue == 0 || originalValue === '0.00') {
                return '-';
            }
            if( originalValue > 0 && calculatedValue <= 0.01){
                 calculatedValue = 0.01;
            }

            return originalValue + "<br>" + calculatedValue;
        }

        if(isNumber(data.crack_ratio_1d)){
            crack_ratio_1d = data.crack_ratio_1d.safeToFixed(2) || 0;
            const calculated_ratio = data.crack_ratio_1d ? ((data.crack_ratio_1d * 0.25 / area) * 100) : 0.00;
            data.crack_ratio_1d = makeTwoLineValue(crack_ratio_1d, calculated_ratio);
        }
        if(isNumber(data.crack_ratio_2d)){
            crack_ratio_2d = data.crack_ratio_2d.safeToFixed(2) || 0;
            const calculated_ratio = data.crack_ratio_2d ? ((data.crack_ratio_2d / area) * 100) : 0.00;
            data.crack_ratio_2d = makeTwoLineValue(crack_ratio_2d, calculated_ratio);
        }

        if(isNumber(surface_damage_ratio_org)){
            const calculated_ratio = surface_damage_ratio_org ? ((surface_damage_ratio_org / area) * 100) : 0.00;
            data.surface_damage_ratio = makeTwoLineValue(surface_damage_ratio_org, calculated_ratio);
        } else {
            data.surface_damage_ratio = surface_damage_ratio_org;
        }
        if (isNumber(data.leak_ratio)) {
            const leak_ratio_org = data.leak_ratio;
            const calculated_ratio = data.leak_ratio ? ((data.leak_ratio / area) * 100) : 0.00;
            data.leak_ratio = makeTwoLineValue(leak_ratio_org, calculated_ratio);
        }
        if (isNumber(data.rebar_corrosion_ratio)) {
            const rebar_corrosion_ratio_org = data.rebar_corrosion_ratio;
            const calculated_ratio = data.rebar_corrosion_ratio ? ((data.rebar_corrosion_ratio / area) * 100) : 0.00;
            data.rebar_corrosion_ratio = makeTwoLineValue(rebar_corrosion_ratio_org, calculated_ratio);
        }
        if (isNumber(data.paint_damage)) {
            const paint_damage_org = data.paint_damage;
            const calculated_ratio = data.paint_damage ? ((data.paint_damage / area) * 100) : 0.00;
            data.paint_damage = makeTwoLineValue(paint_damage_org, calculated_ratio);
        }
        if (isNumber(data.corrosion_ratio)) {
            const corrosion_ratio_org = data.corrosion_ratio;
            const calculated_ratio = data.corrosion_ratio ? ((data.corrosion_ratio / area) * 100) : 0.00;
            data.corrosion_ratio = makeTwoLineValue(corrosion_ratio_org, calculated_ratio);
        }
        if (isNumber(data.damage_ratio)) {
            const damage_ratio_org = data.damage_ratio;
            const calculated_ratio = data.damage_ratio ? ((data.damage_ratio / area) * 100) : 0.00;
            data.damage_ratio = makeTwoLineValue(damage_ratio_org, calculated_ratio);
        }







        switch(componentType) {
            case 'slab':
                let slabtype= $("#slabType").val() ;

                if (slabtype === 'STEEL') {
                    // 강 바닥판 데이터 처리 - 새로운 데이터 구조 사용
                    const componentCrack = (data.component_crack !== undefined && data.component_crack !== null && data.component_crack !== '') ? data.component_crack : '-';
                    const deformationFracture = (data.deformation_fracture !== undefined && data.deformation_fracture !== null && data.deformation_fracture !== '') ? data.deformation_fracture : '-';
                    const boltLoosening = (data.bolt_loosening !== undefined && data.bolt_loosening !== null && data.bolt_loosening !== '') ? data.bolt_loosening : '-';
                    const weldDefect = (data.weld_defect !== undefined && data.weld_defect !== null && data.weld_defect !== '') ? data.weld_defect : '-';
                    const surfaceDeterioration = (data.surface_deterioration_ratio !== undefined && data.surface_deterioration_ratio !== null && data.surface_deterioration_ratio !== '') ? data.surface_deterioration_ratio : '-';

                    // 등급 평가 - 데이터가 비어있으면 'a', 있으면 내용에 따른 평가
                    const componentCrackGrade = componentCrack === '-' ? 'a' : (componentCrack.length > 0 ? 'c' : 'a');
                    const deformationFractureGrade = deformationFracture === '-' ? 'a' : (deformationFracture.length > 0 ? 'c' : 'a');
                    const boltLooseningGrade = boltLoosening === '-' ? 'a' : (boltLoosening.length > 0 ? 'c' : 'a');
                    const weldDefectGrade = weldDefect === '-' ? 'a' : (weldDefect.length > 0 ? 'c' : 'a');
                    const surfaceDeteriorationGrade = surfaceDeterioration === '-' ? 'a' : evaluateGrade(surfaceDeterioration, 'surface_damage_ratio');

                    return `
                        <tr>
                            <td>${spanId}</td>
                            <td><input type="number" class="form-control area-input" value="${inspectionArea}" step="0.1"></td>
                            <td>${componentCrack}</td>
                            <td>${componentCrackGrade}</td>
                            <td>${deformationFracture}</td>
                            <td>${deformationFractureGrade}</td>
                            <td>${boltLoosening}</td>
                            <td>${boltLooseningGrade}</td>
                            <td>${weldDefect}</td>
                            <td>${weldDefectGrade}</td>
                            <td>${surfaceDeterioration === '-' ? '-' : parseFloat(surfaceDeterioration).safeToFixed(2)}</td>
                            <td>${surfaceDeteriorationGrade}</td>
                            <td><strong>${calculateWorstGrade(componentCrackGrade, deformationFractureGrade, boltLooseningGrade, weldDefectGrade, surfaceDeteriorationGrade)}</strong></td>
                        </tr>
                    `;
                } else {
                    // 바닥판 타입에 따른 균열폭 등급 평가 타입 결정
                    const crackWidthType = slabtype === 'PSC' ? 'crack_width_psc' : 'crack_width';

                    return `
                    <tr>
                                <td>${spanId}</td>
                                <td><input type="number" class="form-control area-input" value="${area}" step="0.1"></td>
                                <td>${data.crack_width_1d || '-'}</td>
                                <td>${evaluateGrade(data.crack_width_1d, crackWidthType)}</td>
                                <td data-original-value="${data.original_crack_length_1d || 0}">${data.crack_ratio_1d === 0 || data.crack_ratio_1d === '0.00' ? '-' : data.crack_ratio_1d}</td>
                                <td>${evaluateGrade(data.crack_ratio_1d, 'crack_ratio')}</td>
                                <td>${data.crack_width_2d !== null && data.crack_width_2d !== undefined ? (data.crack_width_2d === 0 ? '-' : data.crack_width_2d) : '-'}</td>
                                <td>${evaluateGrade(data.crack_width_2d, crackWidthType)}</td>
                                <td data-original-value="${data.original_crack_length_2d || 0}">${data.crack_ratio_2d === 0 || data.crack_ratio_2d === '0.00' ? '-' : data.crack_ratio_2d}</td>
                                <td>${evaluateGrade(data.crack_ratio_2d, 'crack_ratio')}</td>
                                <td data-original-value="${data.original_leak_quantity || 0}">${data.leak_ratio === 0 || !data.leak_ratio ? '-' : data.leak_ratio}</td>
                                <td>${evaluateGrade(data.leak_ratio, 'leak_ratio')}</td>
                                <td data-original-value="${data.original_surface_damage_quantity || 0}">${data.surface_damage_ratio === 0 || !data.surface_damage_ratio ? '-' : data.surface_damage_ratio}</td><td>${evaluateGrade(data.surface_damage_ratio, 'surface_damage_ratio')}</td>
                                <td data-original-value="${data.original_rebar_corrosion_quantity || 0}">${data.rebar_corrosion_ratio === 0 || !data.rebar_corrosion_ratio ? '-' : data.rebar_corrosion_ratio}</td><td>${evaluateGrade(data.rebar_corrosion_ratio, 'rebar_corrosion_ratio')}</td>
                                <td><strong>${calculateWorstGrade(
                                    evaluateGrade(data.crack_width_1d, crackWidthType),
                                    evaluateGrade(data.crack_ratio_1d, 'crack_ratio'),
                                    evaluateGrade(data.crack_width_2d, crackWidthType),
                                    evaluateGrade(data.crack_ratio_2d, 'crack_ratio'),
                                    evaluateGrade(data.leak_ratio, 'leak_ratio'),
                                    evaluateGrade(data.surface_damage_ratio, 'surface_damage_ratio'),
                                    evaluateGrade(data.rebar_corrosion_ratio, 'rebar_corrosion_ratio')
                                )}</strong></td>
                        </tr>
                    `;

                }


            case 'girder':
                const girderType = $("#girderType").val();
                if (girderType === 'STEEL') {
                    // 강거더 데이터 처리 - 새로운 데이터 구조 사용
                    const componentCrack = (data.component_crack !== undefined && data.component_crack !== null && data.component_crack !== '') ? data.component_crack : '-';
                    const deformationFracture = (data.deformation_fracture !== undefined && data.deformation_fracture !== null && data.deformation_fracture !== '') ? data.deformation_fracture : '-';
                    const boltLoosening = (data.bolt_loosening !== undefined && data.bolt_loosening !== null && data.bolt_loosening !== '') ? data.bolt_loosening : '-';
                    const weldDefect = (data.weld_defect !== undefined && data.weld_defect !== null && data.weld_defect !== '') ? data.weld_defect : '-';
                    const surfaceDeterioration = (data.surface_deterioration_ratio !== undefined && data.surface_deterioration_ratio !== null && data.surface_deterioration_ratio !== '') ? data.surface_deterioration_ratio : '-';

                    // 등급 평가 - 데이터가 비어있으면 'a', 있으면 내용에 따른 평가
                    const componentCrackGrade = componentCrack === '-' ? 'a' : (componentCrack.length > 0 ? 'c' : 'a');
                    const deformationFractureGrade = deformationFracture === '-' ? 'a' : (deformationFracture.length > 0 ? 'c' : 'a');
                    const boltLooseningGrade = boltLoosening === '-' ? 'a' : (boltLoosening.length > 0 ? 'c' : 'a');
                    const weldDefectGrade = weldDefect === '-' ? 'a' : (weldDefect.length > 0 ? 'c' : 'a');
                    const surfaceDeteriorationGrade = surfaceDeterioration === '-' ? 'a' : evaluateGrade(surfaceDeterioration, 'surface_damage_ratio');

                    return `
                        <tr>
                            <td>${spanId}</td>
                            <td><input type="number" class="form-control area-input" value="${inspectionArea}" step="0.1"></td>
                            <td>${componentCrack}</td>
                            <td>${componentCrackGrade}</td>
                            <td>${deformationFracture}</td>
                            <td>${deformationFractureGrade}</td>
                            <td>${boltLoosening}</td>
                            <td>${boltLooseningGrade}</td>
                            <td>${weldDefect}</td>
                            <td>${weldDefectGrade}</td>
                            <td>${surfaceDeterioration === '-' ? '-' : parseFloat(surfaceDeterioration).safeToFixed(2)}</td>
                            <td>${surfaceDeteriorationGrade}</td>
                            <td><strong>${calculateWorstGrade(componentCrackGrade, deformationFractureGrade, boltLooseningGrade, weldDefectGrade, surfaceDeteriorationGrade)}</strong></td>
                        </tr>
                    `;
                }
                // 거더 타입에 따른 균열폭 등급 평가 타입 결정
                const crackWidthType = girderType === 'PSC' ? 'crack_width_psc' : 'crack_width';

                return `
                    <tr>
                        <td>${spanId}</td>
                        <td><input type="number" class="form-control area-input" value="${inspectionArea}" step="0.1"></td>
                        <td>${data.crack_width_1d || '-'}</td>
                        <td>${evaluateGrade(data.crack_width_1d, crackWidthType)}</td>
                        <td data-original-value="${data.original_crack_length_1d || 0}">${data.crack_ratio_1d === 0 || data.crack_ratio_1d === '0.00' ? '-' : data.crack_ratio_1d}</td>
                        <td>${evaluateGrade(data.crack_ratio_1d, 'crack_ratio')}</td>
                        <td>${data.crack_width_2d !== null && data.crack_width_2d !== undefined ? (data.crack_width_2d === 0 ? '-' : data.crack_width_2d) : '-'}</td>
                        <td>${evaluateGrade(data.crack_width_2d, crackWidthType)}</td>
                        <td data-original-value="${data.original_crack_length_2d || 0}">${data.crack_ratio_2d === 0 || data.crack_ratio_2d === '0.00' ? '-' : data.crack_ratio_2d}</td>
                        <td>${evaluateGrade(data.crack_ratio_2d, 'crack_ratio')}</td>
                        <td data-original-value="${data.original_leak_quantity || 0}">${data.leak_ratio === 0 || !data.leak_ratio ? '-' : data.leak_ratio}</td>
                        <td>${evaluateGrade(data.leak_ratio, 'leak_ratio')}</td>
                        <td data-original-value="${data.original_surface_damage_quantity || 0}">${data.surface_damage_ratio === 0 || !data.surface_damage_ratio ? '-' : data.surface_damage_ratio}</td><td>${evaluateGrade(data.surface_damage_ratio, 'surface_damage_ratio')}</td>
                        <td data-original-value="${data.original_rebar_corrosion_quantity || 0}">${data.rebar_corrosion_ratio === 0 || !data.rebar_corrosion_ratio ? '-' : data.rebar_corrosion_ratio}</td><td>${evaluateGrade(data.rebar_corrosion_ratio, 'rebar_corrosion_ratio')}</td>
                        <td><strong>${calculateWorstGrade(
                            evaluateGrade(data.crack_width_1d, crackWidthType),
                            evaluateGrade(data.crack_ratio_1d, 'crack_ratio'),
                            evaluateGrade(data.crack_width_2d, crackWidthType),
                            evaluateGrade(data.crack_ratio_2d, 'crack_ratio'),
                            evaluateGrade(data.leak_ratio, 'leak_ratio'),
                            evaluateGrade(data.surface_damage_ratio, 'surface_damage_ratio'),
                            evaluateGrade(data.rebar_corrosion_ratio, 'rebar_corrosion_ratio')
                        )}</strong></td>
                    </tr>
                `;
            case 'crossbeam':
                const crossbeamType = $("#crossbeamType").val();
                if (crossbeamType === 'STEEL') {
                    // 표 1.17 구조로 생성 - 새로운 데이터 구조 사용
                    const componentCrack = (data.component_crack !== undefined && data.component_crack !== null && data.component_crack !== '') ? data.component_crack : '-';
                    const deformationFracture = (data.deformation_fracture !== undefined && data.deformation_fracture !== null && data.deformation_fracture !== '') ? data.deformation_fracture : '-';
                    const boltLoosening = (data.bolt_loosening !== undefined && data.bolt_loosening !== null && data.bolt_loosening !== '') ? data.bolt_loosening : '-';
                    const weldDefect = (data.weld_defect !== undefined && data.weld_defect !== null && data.weld_defect !== '') ? data.weld_defect : '-';
                    const surfaceDeterioration = (data.surface_deterioration_ratio !== undefined && data.surface_deterioration_ratio !== null && data.surface_deterioration_ratio !== '') ? data.surface_deterioration_ratio : '-';

                    // 등급 평가 - 데이터가 비어있으면 'a', 있으면 내용에 따른 평가
                    const componentCrackGrade = componentCrack === '-' ? 'a' : (componentCrack.length > 0 ? 'c' : 'a');
                    const deformationFractureGrade = deformationFracture === '-' ? 'a' : (deformationFracture.length > 0 ? 'c' : 'a');
                    const boltLooseningGrade = boltLoosening === '-' ? 'a' : (boltLoosening.length > 0 ? 'c' : 'a');
                    const weldDefectGrade = weldDefect === '-' ? 'a' : (weldDefect.length > 0 ? 'c' : 'a');
                    const surfaceDeteriorationGrade = surfaceDeterioration === '-' ? 'a' : evaluateGrade(surfaceDeterioration, 'surface_damage_ratio');

                    return `
                        <tr>
                            <td>${spanId}</td>
                            <td><input type="number" class="form-control area-input" value="${inspectionArea}" step="0.1"></td>
                            <td>${componentCrack}</td>
                            <td>${componentCrackGrade}</td>
                            <td>${deformationFracture}</td>
                            <td>${deformationFractureGrade}</td>
                            <td>${boltLoosening}</td>
                            <td>${boltLooseningGrade}</td>
                            <td>${weldDefect}</td>
                            <td>${weldDefectGrade}</td>
                            <td>${surfaceDeterioration === '-' ? '-' : parseFloat(surfaceDeterioration).safeToFixed(2)}</td>
                            <td>${surfaceDeteriorationGrade}</td>
                            <td><strong>${calculateWorstGrade(componentCrackGrade, deformationFractureGrade, boltLooseningGrade, weldDefectGrade, surfaceDeteriorationGrade)}</strong></td>
                        </tr>
                    `;
                }
                return `
                    <tr>
                        <td>${spanId}</td>
                        <td><input type="number" class="form-control area-input" value="${inspectionArea}" step="0.1"></td>
                        <td>${data.crack_width_1d || '-'}</td>
                        <td>${evaluateGrade(data.crack_width_1d, 'crack_width')}</td>
                        <td data-original-value="${data.original_crack_length_1d || 0}">${data.crack_ratio_1d === 0 || data.crack_ratio_1d === '0.00' ? '-' : data.crack_ratio_1d}</td>
                        <td>${evaluateGrade(data.crack_ratio_1d, 'crack_ratio')}</td>
                        <td>${data.crack_width_2d !== null && data.crack_width_2d !== undefined ? (data.crack_width_2d === 0 ? '-' : data.crack_width_2d) : '-'}</td>
                        <td>${evaluateGrade(data.crack_width_2d, 'crack_width')}</td>
                        <td data-original-value="${data.original_crack_length_2d || 0}">${data.crack_ratio_2d === 0 || data.crack_ratio_2d === '0.00' ? '-' : data.crack_ratio_2d}</td>
                        <td>${evaluateGrade(data.crack_ratio_2d, 'crack_ratio')}</td>
                        <td data-original-value="${data.original_leak_quantity || 0}">${data.leak_ratio === 0 || !data.leak_ratio ? '-' : data.leak_ratio}</td>
                        <td>${evaluateGrade(data.leak_ratio, 'leak_ratio')}</td>
                        <td data-original-value="${data.original_surface_damage_quantity || 0}">${data.surface_damage_ratio === 0 || !data.surface_damage_ratio ? '-' : data.surface_damage_ratio}</td><td>${evaluateGrade(data.surface_damage_ratio, 'surface_damage_ratio')}</td>
                        <td data-original-value="${data.original_rebar_corrosion_quantity || 0}">${data.rebar_corrosion_ratio === 0 || !data.rebar_corrosion_ratio ? '-' : data.rebar_corrosion_ratio}</td><td>${evaluateGrade(data.rebar_corrosion_ratio, 'rebar_corrosion_ratio')}</td>
                        <td><strong>${calculateWorstGrade(
                            evaluateGrade(data.crack_width_1d, 'crack_width'),
                            evaluateGrade(data.crack_ratio_1d, 'crack_ratio'),
                            evaluateGrade(data.crack_width_2d, 'crack_width'),
                            evaluateGrade(data.crack_ratio_2d, 'crack_ratio'),
                            evaluateGrade(data.leak_ratio, 'leak_ratio'),
                            evaluateGrade(data.surface_damage_ratio, 'surface_damage_ratio'),
                            evaluateGrade(data.rebar_corrosion_ratio, 'rebar_corrosion_ratio')
                        )}</strong></td>
                    </tr>
                `;
            case 'abutment':
                return `
                    <tr>
                        <td>${spanId}</td>
                        <td><input type="number" class="form-control area-input" value="${area}" step="0.1"></td>
                        <td>${data.crack_width || '-'}</td><td>${evaluateGrade(data.crack_width, 'crack_width')}</td>
                        <td>${data.deformation || '-'}</td><td>${data.deformation !== '-' ? 'b' : 'a'}</td>
                        <td data-original-value="${data.original_surface_damage_quantity || 0}">${data.surface_damage_ratio === 0 || !data.surface_damage_ratio ? '-' : data.surface_damage_ratio}</td><td>${evaluateGrade(data.surface_damage_ratio, 'surface_damage_ratio')}</td>
                        <td data-original-value="${data.original_rebar_corrosion_quantity || 0}">${data.rebar_corrosion_ratio === 0 || !data.rebar_corrosion_ratio ? '-' : data.rebar_corrosion_ratio}</td><td>${evaluateGrade(data.rebar_corrosion_ratio, 'rebar_corrosion_ratio')}</td>
                        <td><strong>${calculateWorstGrade(
                                        evaluateGrade(data.crack_width, 'crack_width'),
                                        data.deformation !== '-' ? 'b' : 'a',
                            evaluateGrade(data.surface_damage_ratio, 'surface_damage_ratio'),
                            evaluateGrade(data.rebar_corrosion_ratio, 'rebar_corrosion_ratio')
                        )}</strong></td>
                    </tr>
            `;
            case 'pier':
                return `
                    <tr>
                        <td>${spanId}</td>
                        <td><input type="number" class="form-control area-input" value="${area}" step="0.1"></td>
                        <td>${data.crack_width || '-'}</td><td>${evaluateGrade(data.crack_width, 'crack_width')}</td>
                        <td>${data.deformation || '-'}</td><td>${data.deformation !== '-' ? 'b' : 'a'}</td>
                        <td data-original-value="${data.original_surface_damage_quantity || 0}">${data.surface_damage_ratio === 0 || !data.surface_damage_ratio ? '-' : data.surface_damage_ratio}</td><td>${evaluateGrade(data.surface_damage_ratio, 'surface_damage_ratio')}</td>
                        <td data-original-value="${data.original_rebar_corrosion_quantity || 0}">${data.rebar_corrosion_ratio === 0 || !data.rebar_corrosion_ratio ? '-' : data.rebar_corrosion_ratio}</td><td>${evaluateGrade(data.rebar_corrosion_ratio, 'rebar_corrosion_ratio')}</td>
                        <td><strong>${calculateWorstGrade(
                                        evaluateGrade(data.crack_width, 'crack_width'),
                                        data.deformation !== '-' ? 'b' : 'a',
                            evaluateGrade(data.surface_damage_ratio, 'surface_damage_ratio'),
                            evaluateGrade(data.rebar_corrosion_ratio, 'rebar_corrosion_ratio')
                        )}</strong></td>
                </tr>
            `;
            case 'foundation':
                // 기초 단면손상 등급 계산 (철근노출 포함 여부에 따라 등급 결정)
                let foundation_damage_grade = 'a';
                if (data.damage_condition && data.damage_condition !== '-') {
                    // 철근노출이 포함된 경우 더 높은 등급
                    if (data.damage_condition.includes('철근노출') || data.damage_condition.includes('철근부식')) {
                        foundation_damage_grade = 'd';  // 철근노출은 d등급
                    } else {
                        foundation_damage_grade = 'c';  // 일반 단면손상은 c등급
                    }
                }

                return `
                    <tr>
                        <td>${spanId}</td>
                        <td>${data.crack_width || '-'}</td><td>${evaluateGrade(data.crack_width, 'crack_width')}</td>
                        <td>${data.damage_condition || '-'}</td><td>${foundation_damage_grade}</td>
                        <td>${data.erosion || '-'}</td><td>${data.erosion !== '-' ? 'b' : 'a'}</td>
                        <td>${data.settlement || '-'}</td><td>${data.settlement !== '-' ? 'b' : 'a'}</td>
                        <td><strong>${calculateWorstGrade(
                            evaluateGrade(data.crack_width, 'crack_width'),
                            foundation_damage_grade,
                            data.erosion !== '-' ? 'b' : 'a',
                            data.settlement !== '-' ? 'b' : 'a'
                        )}</strong></td>
                </tr>
                `;
            case 'bearing':
                // section_damage에 철근노출/철근부식이 포함된 경우 c등급, 그 외 단면손상은 b등급, 손상 없으면 a등급
                let bearingSectionGrade = 'a';
                if (data.section_damage && data.section_damage !== '-') {
                    if (data.section_damage.includes('철근노출') || data.section_damage.includes('철근부식')) {
                        bearingSectionGrade = 'c';
                    } else {
                        bearingSectionGrade = 'b';
                    }
                }
                return `
                    <tr>
                        <td>${spanId}</td>
                        <td>${data.body_condition || '-'}</td>
                        <td>${data.body_condition !== '-' ? 'b' : 'a'}</td>
                        <td>${data.crack_width || '-'}</td>
                        <td>${evaluateGrade(data.crack_width, 'crack_width')}</td>
                        <td>${data.section_damage || '-'}</td>
                        <td>${bearingSectionGrade}</td>
                        <td><strong>${calculateWorstGrade(
                            data.body_condition !== '-' ? 'b' : 'a',
                            evaluateGrade(data.crack_width, 'crack_width'),
                            bearingSectionGrade
                        )}</strong></td>
                </tr>
                `;
            case 'expansionJoint':
                // 후타재 단면손상에 철근노출/철근부식이 포함된 경우 c등급, 그 외 단면손상은 b등급, 손상 없으면 a등급
                let expansionSectionGrade = 'a';
                if (data.section_damage && data.section_damage !== '-') {
                    if (data.section_damage.includes('철근노출') || data.section_damage.includes('철근부식')) {
                        expansionSectionGrade = 'c';
                    } else {
                        expansionSectionGrade = 'b';
                    }
                }

                // 후타재 균열 등급 계산 (실제 균열폭 기준)
                let expansionCrackGrade = 'a';
                if (data.footer_crack && data.footer_crack !== '-') {
                    // footer_crack이 실제 균열폭 값인 경우
                    if (typeof data.footer_crack === 'number' || !isNaN(parseFloat(data.footer_crack))) {
                        expansionCrackGrade = evaluateGrade(parseFloat(data.footer_crack), 'crack_width');
                    } else {
                        // footer_crack이 '균열' 문자열인 경우
                        expansionCrackGrade = 'b';
                    }
                }



                // 신축이음 상태평가 플래그 추출
                const flags = extractExpansionJointFlags(data);

                // 신축이음 상태평가 등급 계산
                let joingrade = evaluateExpansionJoint(
                    flags.aging_or_dirt,
                    flags.function_degradation,
                    flags.impact_or_noise,
                    flags.structural_damage,
                    flags.other_damage
                );
                return `
                    <tr>
                        <td>${spanId}</td>
                        <td>${data.body_condition || '-'}</td>
                        <td>${joingrade}</td>
                        <td>${data.footer_crack || '-'}</td>
                        <td>${expansionCrackGrade}</td>
                        <td>${data.section_damage || '-'}</td>
                        <td>${expansionSectionGrade}</td>
                        <td><strong>${calculateWorstGrade(
                            joingrade,  // 실제 평가된 등급 사용
                            expansionCrackGrade,
                            expansionSectionGrade
                        )}</strong></td>
                </tr>
            `;
            case 'pavement':
                // 배수시설 테이블에서 해당 경간의 손상 데이터 확인
                let drainageStatus = '양호';
                let pavementDrainageGrade = 'a';

                // 전역 배수시설 데이터에서 해당 경간 찾기
                if (typeof get_span_damage !== 'undefined' && Array.isArray(get_span_damage)) {
                    const drainageData = get_span_damage.find(d => d.spanId === spanId && d.type === 'drainage');
                    if (drainageData && drainageData.outlet_condition) {
                        drainageStatus = drainageData.outlet_condition;
                        // evaluatePavementDrainage 함수 사용하여 등급 계산
                        if (typeof evaluatePavementDrainage === 'function') {
                            pavementDrainageGrade = evaluatePavementDrainage(drainageStatus);
                        } else {
                            // 기본 로직: 배수구 막힘은 b등급, 기타 손상은 c등급
                            if (drainageStatus.includes('막힘')) {
                                pavementDrainageGrade = 'b';
                            } else if (drainageStatus !== '양호' && drainageStatus !== '-') {
                                pavementDrainageGrade = 'c';
                            }
                        }
                    }
                }

                // 기존 포장 데이터도 고려
                if (data.drainage_condition && data.drainage_condition !== '양호') {
                    drainageStatus = data.drainage_condition;
                    if (typeof evaluatePavementDrainage === 'function') {
                        pavementDrainageGrade = evaluatePavementDrainage(drainageStatus);
                    } else {
                        pavementDrainageGrade = 'b';
                    }
                }

                // 포장 타입에 따른 등급 평가 함수 선택
                const pavementType = $("#pavementType").val();
                const damageType = pavementType === 'CONCRETE' ? 'damage_ratio_concrete' : 'damage_ratio_asphalt';

                return `
                    <tr>
                        <td>${spanId}</td>
                        <td><input type="number" class="form-control area-input" value="${area}" step="0.1"></td>
                        <td data-original-value="${data.original_damage_quantity || 0}">
                        ${data.damage_ratio === 0 || !data.damage_ratio ? '-' : data.damage_ratio}</td>
                        <td>${evaluateGrade(data.damage_ratio, damageType)}</td>
                        <td>${data.traffic_condition || '양호'}</td><td>${data.traffic_condition !== '양호' ? 'b' : 'a'}</td>
                        <td>${drainageStatus}</td><td>${pavementDrainageGrade}</td>
                        <td><strong>${calculateWorstGrade(
                            evaluateGrade(data.damage_ratio, damageType),
                            data.traffic_condition !== '양호' ? 'b' : 'a',
                            pavementDrainageGrade
                        )}</strong></td>
                    </tr>
                `;
            case 'drainage':
                // 배수시설 손상상황 조합
                let damageStatus = '-';
                let grade = 'a';

                console.log(`배수시설 ${spanId} 데이터:`, data);

                // 손상 상태 데이터 수집
                let deposit_amount = 'none';
                let leakage = false;
                let corrosion_due_to_leakage = false;
                let outlet_risk = false;
                let damaged_or_aged = false;

                // 손상내용 분석 및 분류
                if (data.outlet_condition && data.outlet_condition !== '-') {
                    damageStatus = data.outlet_condition;

                    if (data.outlet_condition.includes('토사퇴적')) {
                        if (data.outlet_condition.includes('많이') || data.outlet_condition.includes('심각')) {
                            deposit_amount = 'many';
                        } else {
                            deposit_amount = 'some';
                        }
                    }

                    if (data.outlet_condition.includes('누수')) {
                        leakage = true;
                    }

                    if (data.outlet_condition.includes('부식')) {
                        corrosion_due_to_leakage = true;
                    }

                    if (data.outlet_condition.includes('파손') || data.outlet_condition.includes('노후')) {
                        damaged_or_aged = true;
                    }

                    if (data.outlet_condition.includes('위험') || data.outlet_condition.includes('유출구')) {
                        outlet_risk = true;
                    }
                }

                if (data.pipe_condition && data.pipe_condition !== '-') {
                    if (damageStatus !== '-') {
                        damageStatus += ', ' + data.pipe_condition;
                    } else {
                        damageStatus = data.pipe_condition;
                    }

                    if (data.pipe_condition.includes('토사퇴적')) {
                        if (data.pipe_condition.includes('많이') || data.pipe_condition.includes('심각')) {
                            deposit_amount = 'many';
                        } else if (deposit_amount === 'none') {
                            deposit_amount = 'some';
                        }
                    }

                    if (data.pipe_condition.includes('누수')) {
                        leakage = true;
                    }

                    if (data.pipe_condition.includes('부식')) {
                        corrosion_due_to_leakage = true;
                    }

                    if (data.pipe_condition.includes('파손') || data.pipe_condition.includes('노후')) {
                        damaged_or_aged = true;
                    }

                    if (data.pipe_condition.includes('위험') || data.pipe_condition.includes('유출구')) {
                        outlet_risk = true;
                    }
                }

                // evaluateDrainageFacility 함수를 사용하여 등급 계산
                grade = evaluateDrainageFacility(damageStatus);

                // 서버에서 제공된 등급이 있다면 우선 사용
                if (data.grade && data.grade !== 'a') {
                    grade = data.grade;
                }

                console.log(`배수시설 ${spanId} - 손상상황: ${damageStatus}, 등급: ${grade}`);

                return `
                    <tr>
                        <td>${spanId}</td>
                        <td>${damageStatus}</td>
                        <td><strong>${grade}</strong></td>
                </tr>
                `;
            case 'railing':
            return `
            <tr>
            <td>${spanId}</td>
            <td><input type="number" class="form-control area-input" value="${area}" step="0.1"></td>
            <td data-original-value="${data.original_paint_damage || 0}">${data.paint_damage === 0 || !data.paint_damage ? '-' : data.paint_damage}</td><td>${evaluateGrade(data.paint_damage, 'paint_damage_ratio')}</td>
            <td data-original-value="${data.original_corrosion_ratio || 0}">${data.corrosion_ratio === 0 || !data.corrosion_ratio ? '-' : data.corrosion_ratio}</td><td>${evaluateGrade(data.corrosion_ratio, 'sub_rust_area')}</td>

            <td data-original-value="${data.original_damage_ratio || 0}">${data.damage_ratio === 0 || !data.damage_ratio ? '-' : data.damage_ratio}</td><td>${evaluateGrade(data.damage_ratio, 'section_loss_ratio')}</td>

            <td>${data.crack_width || '-'}</td><td>${evaluateGrade(data.crack_width, 'crack_width')}</td>
             <!-- 손상 등급 계산  여기 합치기  7월 25일 수정  -->
            <td data-original-value="${data.total_damage_quantity || 0}">${data.total_damage_quantity === 0 || !data.surface_damage_ratio ? '-' : data.surface_damage_ratio}</td>
            <td>${evaluateGrade(data.surface_damage_ratio, 'surface_damage_ratio')}</td>

            <td><strong>${calculateWorstGrade(
            evaluateGrade(data.paint_damage, 'paint_damage_ratio'),
            evaluateGrade(data.corrosion_ratio, 'sub_rust_area'),
            evaluateGrade(data.damage_ratio, 'section_loss_ratio'),
            evaluateGrade(data.crack_width, 'crack_width'),
            evaluateGrade(data.surface_damage_ratio, 'surface_damage_ratio'),
            evaluateGrade(data.rebar_corrosion_ratio, 'rebar_corrosion_ratio')
            )}</strong></td>
                </tr>
            `;
            default:
                return generateEmptyTableRow(componentType, spanId, inspectionArea);
        }
    }

    // 통합 상태평가 생성
    function generateTotalEvaluationTable(selectedComponents) {
        console.log('통합 상태평가 생성 시작');
        const tableElement = document.getElementById('totalEvaluationTable');
        const spanCount = parseInt(document.getElementById('spanCount').value) || 0;
        //const structureType = document.getElementById('structureType').value;

        const structureType = bridgeData.structureType;

        // 탄산화 시험 위치 데이터 가져오기
        const carbonationUpperPositions = $('#carbonationUpperPositions').val();
        const carbonationLowerPositions = $('#carbonationLowerPositions').val();

        console.log('탄산화 시험 위치 데이터:', {
            upperPositions: carbonationUpperPositions,
            lowerPositions: carbonationLowerPositions
        });

         let tableHtml = `
            <thead>
                <tr>
                    <th rowspan="2">부재의 분류</th>
                    <th rowspan="2">구조형식</th>
                    <th colspan="2">상부구조</th>
                    <th>2차 부재</th>
                    <th colspan="4">기타부재</th>
                    <th>받침</th>
                    <th colspan="2">하부구조</th>
                    <th colspan="4">내구성 요소</th>
                </tr>
                <tr>
                    <th>바닥판</th>
                    <th>거더</th>
                    <th>가로보</th>
                    <th>포장</th>
                    <th>배수</th>
                    <th>난간연석</th>
                    <th>신축이음</th>
                    <th>교량받침</th>
                    <th>하부</th>
                    <th>기초</th>
                    <th>탄산화<br>상부</th>
                    <th>탄산화<br>하부</th>
                    <th>염화물<br>상부</th>
                    <th>염화물<br>하부</th>
                </tr>
            </thead>
            <tbody>
        `;

        // 각 경간별로 부재 등급 수집 및 행 생성
        const spanRows = [];

        // A1(S1) 행 생성
        const a1Grades = {
            slab: getComponentGradeBySpan('slab', 'S1'),
            girder: getComponentGradeBySpan('girder', 'S1'),
            crossbeam: getComponentGradeBySpan('crossbeam', 'S1'),
            pavement: getComponentGradeBySpan('pavement', 'S1'),
            drainage: getComponentGradeBySpan('drainage', 'S1'),
            railing: getComponentGradeBySpan('railing', 'S1'),
            expansionJoint: getComponentGradeBySpan('expansionJoint', 'A1'),
            bearing: getComponentGradeBySpan('bearing', 'A1'),
            abutment: getComponentGradeBySpan('abutment', 'A1'),
            foundation: getComponentGradeBySpan('foundation', 'A1')
        };

        console.log('A1(S1) 등급:', a1Grades);

        // 탄산화 시험 드롭다운 생성 함수
        function createCarbonationDropdown(component, position, isUpper) {
            const positions = isUpper ? carbonationUpperPositions : carbonationLowerPositions;
            console.log(`탄산화 드롭다운 생성: ${component}, ${position}, ${isUpper ? '상부' : '하부'}`);
            console.log(`입력된 위치: ${positions}`);

            if (!positions || positions.trim() === '') {
                console.log('위치 입력이 없음');
                return '-';
            }

            const positionArray = positions.split(',').map(p => p.trim().toUpperCase());
            console.log(`파싱된 위치 배열: ${positionArray}`);

            // 사용자가 입력한 위치에 현재 위치가 포함되어 있는지 확인
            const isSelected = positionArray.includes(position.toUpperCase());
            console.log(`위치 ${position} 포함 여부: ${isSelected}`);

            // 탄산화 상부/하부 컴포넌트가 선택되어 있고, 사용자가 입력한 위치에 해당하는 경우에만 드롭다운 생성
            const componentKey = isUpper ? 'carbonationUpper' : 'carbonationLower';
            const isComponentSelected = selectedComponents[componentKey];
            console.log(`컴포넌트 ${componentKey} 선택 여부: ${isComponentSelected}`);

            if (isSelected && isComponentSelected) {
                console.log(`드롭다운 생성됨: ${componentKey} - ${position}`);
                return `<select class="form-select form-select-sm carbonation-grade" data-component="${componentKey}" data-position="${position}" data-type="${isUpper ? 'upper' : 'lower'}">
                    <option value="">선택</option>
                    <option value="a">a</option>
                    <option value="b">b</option>
                    <option value="c">c</option>
                    <option value="d">d</option>
                    <option value="e">e</option>
                </select>`;
            } else {
                console.log(`드롭다운 생성 안됨: ${componentKey} - ${position}`);
                return '-';
            }
        }

        // A1(S1) 탄산화 시험 드롭다운
        const a1CarbonationUpperDropdown = createCarbonationDropdown('carbonationUpper', 'S1', true);
        const a1CarbonationLowerDropdown = createCarbonationDropdown('carbonationLower', 'A1', false);

            tableHtml += `
                <tr>
                <td>A1(S1)</td>
                <td>${structureType}</td>
                <td>${selectedComponents.slab ? a1Grades.slab : '-'}</td>
                <td>${selectedComponents.girder ? a1Grades.girder : '-'}</td>
                <td>${selectedComponents.crossbeam ? a1Grades.crossbeam : '-'}</td>
                <td>${selectedComponents.pavement ? a1Grades.pavement : '-'}</td>
                <td>${selectedComponents.drainage ? a1Grades.drainage : '-'}</td>
                <td>${selectedComponents.railing ? a1Grades.railing : 'a'}</td>
                <td>${selectedComponents.expansionJoint ? a1Grades.expansionJoint : 'a'}</td>
                <td>${selectedComponents.bearing ? a1Grades.bearing : '-'}</td>
                <td>${selectedComponents.abutment ? a1Grades.abutment : '-'}</td>
                <td>${selectedComponents.foundation ? a1Grades.foundation : '-'}</td>
                <td>${a1CarbonationUpperDropdown}</td>
                <td>${a1CarbonationLowerDropdown}</td>
                <td>-</td>
                <td>-</td>
                </tr>
            `;

        // 중간 경간들 (P1(S2) ~ Pn-1(Sn))
        for (let i = 1; i < spanCount; i++) {
            const pierGrades = {
                slab: getComponentGradeBySpan('slab', `S${i+1}`),
                girder: getComponentGradeBySpan('girder', `S${i+1}`),
                crossbeam: getComponentGradeBySpan('crossbeam', `S${i+1}`),
                pavement: getComponentGradeBySpan('pavement', `S${i+1}`),
                drainage: getComponentGradeBySpan('drainage', `S${i+1}`),
                railing: getComponentGradeBySpan('railing', `S${i+1}`),
                expansionJoint: getComponentGradeBySpan('expansionJoint', `P${i}`),
                bearing: getComponentGradeBySpan('bearing', `P${i}`),
                pier: getComponentGradeBySpan('pier', `P${i}`),
                foundation: getComponentGradeBySpan('foundation', `P${i}`)
            };

            // 탄산화 시험 드롭다운
            const pierCarbonationUpperDropdown = createCarbonationDropdown('carbonationUpper', `S${i+1}`, true);
            const pierCarbonationLowerDropdown = createCarbonationDropdown('carbonationLower', `P${i}`, false);

            tableHtml += `
                <tr>
                <td>P${i}(S${i+1})</td>
                <td>${structureType}</td>
                <td>${selectedComponents.slab ? pierGrades.slab : '-'}</td>
                <td>${selectedComponents.girder ? pierGrades.girder : '-'}</td>
                <td>${selectedComponents.crossbeam ? pierGrades.crossbeam : '-'}</td>
                <td>${selectedComponents.pavement ? pierGrades.pavement : '-'}</td>
                <td>${selectedComponents.drainage ? pierGrades.drainage : '-'}</td>
                <td>${selectedComponents.railing ? pierGrades.railing : '-'}</td>
                <td>${selectedComponents.expansionJoint ? pierGrades.expansionJoint : 'a'}</td>
                <td>${selectedComponents.bearing ? pierGrades.bearing : '-'}</td>
                <td>${selectedComponents.pier ? pierGrades.pier : '-'}</td>
                <td>${selectedComponents.foundation ? pierGrades.foundation : '-'}</td>
                <td>${pierCarbonationUpperDropdown}</td>
                <td>${pierCarbonationLowerDropdown}</td>
                <td>-</td>
                <td>-</td>
                </tr>
            `;
        }

        // A2 행 생성
        const a2Grades = {
            expansionJoint: getComponentGradeBySpan('expansionJoint', 'A2'),
            bearing: getComponentGradeBySpan('bearing', 'A2'),
            abutment: getComponentGradeBySpan('abutment', 'A2'),
            foundation: getComponentGradeBySpan('foundation', 'A2')
        };

        console.log('A2 등급:', a2Grades);

        // A2의 탄산화 시험 드롭다운 (마지막 경간이므로 Sn에 해당)
        const lastSpanId = `S${spanCount}`;
        const a2CarbonationUpperDropdown = createCarbonationDropdown('carbonationUpper', lastSpanId, true);
        const a2CarbonationLowerDropdown = createCarbonationDropdown('carbonationLower', 'A2', false);

        tableHtml += `
            <tr>
                <td>A2</td>
                <td>${structureType}</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>${selectedComponents.expansionJoint ? a2Grades.expansionJoint : 'a'}</td>
                <td>${selectedComponents.bearing ? a2Grades.bearing : '-'}</td>
                <td>${selectedComponents.abutment ? a2Grades.abutment : '-'}</td>
                <td>${selectedComponents.foundation ? a2Grades.foundation : '-'}</td>
                <td>${a2CarbonationUpperDropdown}</td>
                <td>${a2CarbonationLowerDropdown}</td>
                <td>-</td>
                <td>-</td>
            </tr>
        `;

        // 부재별 평균 계산
        const averages = calculateComponentAverages(selectedComponents, spanCount);
        console.log('부재별 평균:', averages);

        // 구조형식에 따른 가중치 자동 선택 (STRUCTURE_WEIGHTS에서 가져오기)
        /*
        let weights = {
            slab: 0, girder: 0, crossbeam: 0, pavement: 0, drainage: 0,
            railing: 0, expansionJoint: 0, bearing: 0, abutment: 0, pier: 0,
            foundation: 0, carbonation_upper: 0, carbonation_lower: 0,
            chloride_upper: 0, chloride_lower: 0
        };
        */



        let weights = {
            slab: Number($('#weightSlab').val()) || 0,
            girder: Number($('#weightGirder').val()) || 0,
            crossbeam: Number($('#weightCrossbeam').val()) || 0,
            pavement: Number($('#weightPavement').val()) || 0,
            drainage: Number($('#weightDrainage').val()) || 0,
            railing: Number($('#weightRailing').val()) || 0,
            expansionJoint: Number($('#weightExpansionJoint').val()) || 0,
            bearing: Number($('#weightBearing').val()) || 0,
            abutment: Number($('#weightAbutment').val()) || 0,
            foundation: Number($('#weightFoundation').val()) || 0,
            carbonation_upper: Number($('#weightCarbonationUpper').val()) || 0,
            carbonation_lower: Number($('#weightCarbonationLower').val()) || 0,





            };


        // STRUCTURE_WEIGHTS에서 해당 구조형식의 가중치 가져오기


        // 가중평균 계산
        const weightedSum = calculateWeightedSum(averages, weights, selectedComponents);
        const totalWeight = calculateTotalWeight(weights, selectedComponents);
        const overallScore = totalWeight > 0 ? (weightedSum / totalWeight).safeToFixed(3) : '0.000';
        const overallGrade = convertScoreToGrade(parseFloat(overallScore));

        console.log('가중합계:', weightedSum, '총가중치:', totalWeight, '점수:', overallScore, '등급:', overallGrade);

        // 탄산화 초기 평균 계산 (기본값 사용)
        const initialCarbonationAverages = {
            upper: 0.0, // 기본값
            lower: 0.0  // 기본값
        };

        console.log('초기 탄산화 평균 (기본값):', initialCarbonationAverages);

        tableHtml += `
            <tr>
                <td colspan="2">평균</td>
                <td>${averages.slab.safeToFixed(3)}</td>
                <td>${averages.girder.safeToFixed(3)}</td>
                <td>${averages.crossbeam.safeToFixed(3)}</td>
                <td>${averages.pavement.safeToFixed(3)}</td>
                <td>${averages.drainage.safeToFixed(3)}</td>
                <td>${averages.railing.safeToFixed(3)}</td>
                <td>${averages.expansionJoint.safeToFixed(3)}</td>
                <td>${averages.bearing.safeToFixed(3)}</td>
                <td>${averages.abutment.safeToFixed(3)}</td>
                <td>${averages.foundation.safeToFixed(3)}</td>
                <td>${initialCarbonationAverages.upper==0.0?'-':initialCarbonationAverages.upper.safeToFixed(3)}</td>
                <td>${initialCarbonationAverages.lower==0.0?'-':initialCarbonationAverages.lower.safeToFixed(3)}</td>
                <td>-</td>
                <td>-</td>
            </tr>
            <tr>
                <td colspan="2">가중치</td>
                <td>${weights.slab==0?'-':weights.slab}</td>
                <td>${weights.girder==0?'-':weights.girder}</td>
                <td>${weights.crossbeam==0?'-':weights.crossbeam}</td>
                <td>${weights.pavement==0?'-':weights.pavement}</td>
                <td>${weights.drainage==0?'-':weights.drainage}</td>
                <td>${weights.railing==0?'-':weights.railing}</td>
                <td>${weights.expansionJoint==0?'-':weights.expansionJoint}</td>
                <td>${weights.bearing==0?'-':weights.bearing}</td>
                <td>${weights.abutment==0?'-':weights.abutment}</td>
                <td>${weights.foundation==0?'-':weights.foundation}</td>
                <td>${weights.carbonation_upper==0?'-':weights.carbonation_upper}</td>
                <td>${weights.carbonation_lower==0?'-':weights.carbonation_lower}</td>
                <td>-</td>
                <td>-</td>
            </tr>
            <tr>
                <td colspan="2">(평균×가중치)/<br>가중치 합</td>
                <td>${((averages.slab * weights.slab) / totalWeight).safeToFixed(3)}</td>
                <td>${((averages.girder * weights.girder) / totalWeight).safeToFixed(3)}</td>
                <td>${((averages.crossbeam * weights.crossbeam) / totalWeight).safeToFixed(3)}</td>
                <td>${((averages.pavement * weights.pavement) / totalWeight).safeToFixed(3)}</td>
                <td>${((averages.drainage * weights.drainage) / totalWeight).safeToFixed(3)}</td>
                <td>${((averages.railing * weights.railing) / totalWeight).safeToFixed(3)}</td>
                <td>${((averages.expansionJoint * weights.expansionJoint) / totalWeight).safeToFixed(3)}</td>
                <td>${((averages.bearing * weights.bearing) / totalWeight).safeToFixed(3)}</td>
                <td>${((averages.abutment * weights.abutment) / totalWeight).safeToFixed(3)}</td>
                <td>${((averages.foundation * weights.foundation) / totalWeight).safeToFixed(3)}</td>
                <td>${((initialCarbonationAverages.upper * weights.carbonation_upper) / totalWeight).safeToFixed(3)}</td>
                <td>${((initialCarbonationAverages.lower * weights.carbonation_lower) / totalWeight).safeToFixed(3)}</td>
                <td>-</td>
                <td>-</td>
            </tr>
            <tr><td colspan="15">환산 결함도 점수</td><td>${overallScore}</td></tr>
            <tr><td colspan="15">상태평가 결과</td><td>${overallGrade}</td></tr>
        `;

        tableHtml += '</tbody>';
        tableElement.innerHTML = tableHtml;

        // 점수 테이블 생성
        generateTotalScoreEvaluationTable(selectedComponents, spanCount, structureType, averages, weights, initialCarbonationAverages, totalWeight);

        // 탄산화 시험 드롭다운 이벤트 리스너 추가 - 이벤트 위임 사용
        $(document).off('change', '.carbonation-grade').on('change', '.carbonation-grade', function() {
            const selectedValue = $(this).val();
            const component = $(this).data('component');
            const position = $(this).data('position');
            const type = $(this).data('type');

            console.log(`탄산화 시험 등급 변경: ${component}, ${position}, ${type}, ${selectedValue}`);

            // 탄산화 등급 변경 시 자동 저장 (디바운싱 적용)
            clearTimeout(window.carbonationSaveTimer);
            window.carbonationSaveTimer = setTimeout(function() {
                saveCarbonationTestData();
            }, 500); // 0.5초 후 저장

            // 탄산화 등급 변경 시 통합산정결과표 재계산
            recalculateTotalEvaluationTable();
        });

        console.log('통합 상태평가 생성 완료');


        // 기존 탄산화 데이터 불러오기 이분에서 계산하기 처리
        loadCarbonationTestData();

        // 통합결과 저장/반영 버튼 이벤트 리스너 추가
        $('#saveTotalEvaluation').off('click').on('click', function() {
            console.log('=== 통합결과 저장/반영 버튼 클릭 ===');
            saveCarbonationTestData();
            recalculateTotalEvaluationTable();
        });

        // 테이블 생성 후 탄산화 계산식 반영
        recalculateTotalEvaluationTable();
    }

    // 점수 테이블 생성 함수
    function generateTotalScoreEvaluationTable(selectedComponents, spanCount, structureType, averages, weights, carbonationAverages, totalWeight) {
        console.log('통합 점수평가 생성 시작');
        const scoreTableElement = document.getElementById('totalScoreEvaluationTable');

        if (!scoreTableElement) {
            console.log('점수 테이블 요소를 찾을 수 없음');
            return;
        }

        // 등급을 점수로 변환하는 함수
        const gradeToScore = (grade) => {
            const gradeMap = { 'a': 0.1, 'b': 0.2, 'c': 0.4, 'd': 0.7, 'e': 1.0 };
            return gradeMap[grade.toLowerCase()] || null;
        };

        let scoreTableHtml = `
            <thead>
                <tr>
                    <th rowspan="2">부재의 분류</th>
                    <th rowspan="2">구조형식</th>
                    <th colspan="2">상부구조</th>
                    <th>2차 부재</th>
                    <th colspan="4">기타부재</th>
                    <th>받침</th>
                    <th colspan="2">하부구조</th>
                    <th colspan="4">내구성 요소</th>
                </tr>
                <tr>
                    <th>바닥판</th>
                    <th>거더</th>
                    <th>가로보</th>
                    <th>포장</th>
                    <th>배수</th>
                    <th>난간연석</th>
                    <th>신축이음</th>
                    <th>교량받침</th>
                    <th>하부</th>
                    <th>기초</th>
                    <th>탄산화<br>상부</th>
                    <th>탄산화<br>하부</th>
                    <th>염화물<br>상부</th>
                    <th>염화물<br>하부</th>
                </tr>
            </thead>
            <tbody>
        `;

        // A1(S1) 행 생성 - 점수로 변환 (선택된 부재만 계산)
        const a1Scores = {
            slab: selectedComponents.slab ? gradeToScore(getComponentGradeBySpan('slab', 'S1')) : null,
            girder: selectedComponents.girder ? gradeToScore(getComponentGradeBySpan('girder', 'S1')) : null,
            crossbeam: selectedComponents.crossbeam ? gradeToScore(getComponentGradeBySpan('crossbeam', 'S1')) : null,
            pavement: selectedComponents.pavement ? gradeToScore(getComponentGradeBySpan('pavement', 'S1')) : null,
            drainage: selectedComponents.drainage ? gradeToScore(getComponentGradeBySpan('drainage', 'S1')) : null,
            railing: selectedComponents.railing ? gradeToScore(getComponentGradeBySpan('railing', 'S1')) : null,
            expansionJoint: selectedComponents.expansionJoint ? gradeToScore(getComponentGradeBySpan('expansionJoint', 'A1')) : null,
            bearing: selectedComponents.bearing ? gradeToScore(getComponentGradeBySpan('bearing', 'A1')) : null,
            abutment: selectedComponents.abutment ? gradeToScore(getComponentGradeBySpan('abutment', 'A1')) : null,
            foundation: selectedComponents.foundation ? gradeToScore(getComponentGradeBySpan('foundation', 'A1')) : null
        };

        // 탄산화 점수 계산 (드롭다운에서 선택된 값 사용)
        const getCarbonationScore = (position, isUpper) => {
            const selector = `.carbonation-grade[data-type="${isUpper ? 'upper' : 'lower'}"][data-position="${position}"]`;
            const dropdown = document.querySelector(selector);
            if (dropdown && dropdown.value) {
                return gradeToScore(dropdown.value);
            }
            return carbonationAverages[isUpper ? 'upper' : 'lower'];
        };

        scoreTableHtml += `
            <tr>
                <td>A1(S1)</td>
                <td>${structureType}</td>
                <td>${a1Scores.slab !== null ? a1Scores.slab.toFixed(1) : '-'}</td>
                <td>${a1Scores.girder !== null ? a1Scores.girder.toFixed(1) : '-'}</td>
                <td>${a1Scores.crossbeam !== null ? a1Scores.crossbeam.toFixed(1) : '-'}</td>
                <td>${a1Scores.pavement !== null ? a1Scores.pavement.toFixed(1) : '-'}</td>
                <td>${a1Scores.drainage !== null ? a1Scores.drainage.toFixed(1) : '-'}</td>
                <td>${a1Scores.railing !== null ? a1Scores.railing.toFixed(1) : '-'}</td>
                <td>${a1Scores.expansionJoint !== null ? a1Scores.expansionJoint.toFixed(1) : '-'}</td>
                <td>${a1Scores.bearing !== null ? a1Scores.bearing.toFixed(1) : '-'}</td>
                <td>${a1Scores.abutment !== null ? a1Scores.abutment.toFixed(1) : '-'}</td>
                <td>${a1Scores.foundation !== null ? a1Scores.foundation.toFixed(1) : '-'}</td>
                <td>${selectedComponents.carbonationUpper ? getCarbonationScore('S1', true).toFixed(1) : '-'}</td>
                <td>${selectedComponents.carbonationLower ? getCarbonationScore('A1', false).toFixed(1) : '-'}</td>
                <td>-</td>
                <td>-</td>
            </tr>
        `;

        // 중간 경간들 (P1(S2) ~ Pn-1(Sn))
        for (let i = 1; i < spanCount; i++) {
            const pierScores = {
                slab: selectedComponents.slab ? gradeToScore(getComponentGradeBySpan('slab', `S${i+1}`)) : null,
                girder: selectedComponents.girder ? gradeToScore(getComponentGradeBySpan('girder', `S${i+1}`)) : null,
                crossbeam: selectedComponents.crossbeam ? gradeToScore(getComponentGradeBySpan('crossbeam', `S${i+1}`)) : null,
                pavement: selectedComponents.pavement ? gradeToScore(getComponentGradeBySpan('pavement', `S${i+1}`)) : null,
                drainage: selectedComponents.drainage ? gradeToScore(getComponentGradeBySpan('drainage', `S${i+1}`)) : null,
                railing: selectedComponents.railing ? gradeToScore(getComponentGradeBySpan('railing', `S${i+1}`)) : null,
                expansionJoint: selectedComponents.expansionJoint ? gradeToScore(getComponentGradeBySpan('expansionJoint', `P${i}`)) : null,
                bearing: selectedComponents.bearing ? gradeToScore(getComponentGradeBySpan('bearing', `P${i}`)) : null,
                pier: selectedComponents.pier ? gradeToScore(getComponentGradeBySpan('pier', `P${i}`)) : null,
                foundation: selectedComponents.foundation ? gradeToScore(getComponentGradeBySpan('foundation', `P${i}`)) : null
            };

            scoreTableHtml += `
                <tr>
                    <td>P${i}(S${i+1})</td>
                    <td>${structureType}</td>
                    <td>${pierScores.slab !== null ? pierScores.slab.toFixed(1) : '-'}</td>
                    <td>${pierScores.girder !== null ? pierScores.girder.toFixed(1) : '-'}</td>
                    <td>${pierScores.crossbeam !== null ? pierScores.crossbeam.toFixed(1) : '-'}</td>
                    <td>${pierScores.pavement !== null ? pierScores.pavement.toFixed(1) : '-'}</td>
                    <td>${pierScores.drainage !== null ? pierScores.drainage.toFixed(1) : '-'}</td>
                    <td>${pierScores.railing !== null ? pierScores.railing.toFixed(1) : '-'}</td>
                    <td>${pierScores.expansionJoint !== null ? pierScores.expansionJoint.toFixed(1) : '-'}</td>
                    <td>${pierScores.bearing !== null ? pierScores.bearing.toFixed(1) : '-'}</td>
                    <td>${pierScores.pier !== null ? pierScores.pier.toFixed(1) : '-'}</td>
                    <td>${pierScores.foundation !== null ? pierScores.foundation.toFixed(1) : '-'}</td>
                    <td>${selectedComponents.carbonationUpper ? getCarbonationScore(`S${i+1}`, true).toFixed(1)==0.0?  '-' : getCarbonationScore(`S${i+1}`, true).toFixed(1) : '-'}</td>
                    <td>${selectedComponents.carbonationLower ? getCarbonationScore(`P${i}`, false).toFixed(1)==0.0?  '-' : getCarbonationScore(`P${i}`, false).toFixed(1) : '-'}</td>
                    <td>-</td>
                    <td>-</td>
                </tr>
            `;
        }

        // A2 행 생성 - 점수로 변환 (선택된 부재만 계산)
        const a2Scores = {
            expansionJoint: selectedComponents.expansionJoint ? gradeToScore(getComponentGradeBySpan('expansionJoint', 'A2')) : null,
            bearing: selectedComponents.bearing ? gradeToScore(getComponentGradeBySpan('bearing', 'A2')) : null,
            abutment: selectedComponents.abutment ? gradeToScore(getComponentGradeBySpan('abutment', 'A2')) : null,
            foundation: selectedComponents.foundation ? gradeToScore(getComponentGradeBySpan('foundation', 'A2')) : null
        };

        const lastSpanId = `S${spanCount}`;

        scoreTableHtml += `
            <tr>
                <td>A2</td>
                <td>${structureType}</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>${a2Scores.expansionJoint !== null ? a2Scores.expansionJoint.toFixed(1) : '-'}</td>
                <td>${a2Scores.bearing !== null ? a2Scores.bearing.toFixed(1) : '-'}</td>
                <td>${a2Scores.abutment !== null ? a2Scores.abutment.toFixed(1) : '-'}</td>
                <td>${a2Scores.foundation !== null ? a2Scores.foundation.toFixed(1) : '-'}</td>
                <td>${selectedComponents.carbonationUpper ? getCarbonationScore(lastSpanId, true).toFixed(1) : '-'}</td>
                <td>${selectedComponents.carbonationLower ? getCarbonationScore('A2', false).toFixed(1) : '-'}</td>
                <td>-</td>
                <td>-</td>
            </tr>
        `;

        // 평균행 추가
        scoreTableHtml += `
            <tr>
                <td colspan="2">평균</td>
                <td>${averages.slab.safeToFixed(3)}</td>
                <td>${averages.girder.safeToFixed(3)}</td>
                <td>${averages.crossbeam.safeToFixed(3)}</td>
                <td>${averages.pavement.safeToFixed(3)}</td>
                <td>${averages.drainage.safeToFixed(3)}</td>
                <td>${averages.railing.safeToFixed(3)}</td>
                <td>${averages.expansionJoint.safeToFixed(3)}</td>
                <td>${averages.bearing.safeToFixed(3)}</td>
                <td>${averages.abutment.safeToFixed(3)}</td>
                <td>${averages.foundation.safeToFixed(3)}</td>
                <td>${carbonationAverages.upper.safeToFixed(3)}</td>
                <td>${carbonationAverages.lower.safeToFixed(3)}</td>
                <td>-</td>
                <td>-</td>
            </tr>
            <tr>
                <td colspan="2">가중치</td>
                <td>${weights.slab==0?'-':weights.slab}</td>
                <td>${weights.girder==0?'-':weights.girder}</td>
                <td>${weights.crossbeam==0?'-':weights.crossbeam}</td>
                <td>${weights.pavement==0?'-':weights.pavement}</td>
                <td>${weights.drainage==0?'-':weights.drainage}</td>
                <td>${weights.railing==0?'-':weights.railing}</td>
                <td>${weights.expansionJoint==0?'-':weights.expansionJoint}</td>
                <td>${weights.bearing==0?'-':weights.bearing}</td>
                <td>${weights.abutment==0?'-':weights.abutment}</td>
                <td>${weights.foundation==0?'-':weights.foundation}</td>
                <td>${weights.carbonation_upper==0?'-':weights.carbonation_upper}</td>
                <td>${weights.carbonation_lower==0?'-':weights.carbonation_lower}</td>
                <td>-</td>
                <td>-</td>
            </tr>
            <tr>
                <td colspan="2">(평균×가중치)/<br>가중치 합</td>
                <td>${((averages.slab * weights.slab) / totalWeight).safeToFixed(3)}</td>
                <td>${((averages.girder * weights.girder) / totalWeight).safeToFixed(3)}</td>
                <td>${((averages.crossbeam * weights.crossbeam) / totalWeight).safeToFixed(3)}</td>
                <td>${((averages.pavement * weights.pavement) / totalWeight).safeToFixed(3)}</td>
                <td>${((averages.drainage * weights.drainage) / totalWeight).safeToFixed(3)}</td>
                <td>${((averages.railing * weights.railing) / totalWeight).safeToFixed(3)}</td>
                <td>${((averages.expansionJoint * weights.expansionJoint) / totalWeight).safeToFixed(3)}</td>
                <td>${((averages.bearing * weights.bearing) / totalWeight).safeToFixed(3)}</td>
                <td>${((averages.abutment * weights.abutment) / totalWeight).safeToFixed(3)}</td>
                <td>${((averages.foundation * weights.foundation) / totalWeight).safeToFixed(3)}</td>
                <td>${((carbonationAverages.upper * weights.carbonation_upper) / totalWeight).safeToFixed(3)}</td>
                <td>${((carbonationAverages.lower * weights.carbonation_lower) / totalWeight).safeToFixed(3)}</td>
                <td>-</td>
                <td>-</td>
            </tr>
        `;

        // 최종 점수 및 등급 계산
        const weightedSum = calculateWeightedSum(averages, weights, selectedComponents);
        const overallScore = totalWeight > 0 ? (weightedSum / totalWeight).safeToFixed(3) : '0.000';
        const overallGrade = convertScoreToGrade(parseFloat(overallScore));

        scoreTableHtml += `
            <tr><td colspan="15">환산 결함도 점수</td><td>${overallScore}</td></tr>
            <tr><td colspan="15">상태평가 결과</td><td>${overallGrade}</td></tr>
        `;

        scoreTableHtml += '</tbody>';
        scoreTableElement.innerHTML = scoreTableHtml;

        console.log('통합 점수평가 생성 완료');
    }

    // 특정 경간의 부재별 등급 가져오기 함수
    function getComponentGradeBySpan(component, spanId) {
        console.log(`${component} 부재의 ${spanId} 경간 등급 조회`);

        const tableElement = document.getElementById(`${component}EvaluationTable`);
        if (!tableElement) {
            console.log(`${component}EvaluationTable 테이블을 찾을 수 없음`);
            return '-';
        }

        const tbody = tableElement.getElementsByTagName('tbody')[0];
        if (!tbody) {
            console.log(`${component}EvaluationTable tbody를 찾을 수 없음`);
            return '-';
        }

        const rows = tbody.getElementsByTagName('tr');
        for (let i = 0; i < rows.length; i++) {
            const cells = rows[i].cells;
            if (cells.length > 0) {
                const cellSpanId = cells[0].textContent.trim();
                if (cellSpanId === spanId) {
                    // 마지막 셀에서 등급 추출 (strong 태그 내부)
                    const lastCell = cells[cells.length - 1];
                    const strongElement = lastCell.querySelector('strong');
                    if (strongElement) {
                        const grade = strongElement.textContent.trim().toLowerCase();
                        console.log(`${component} ${spanId} 등급 발견: ${grade}`);
                        return ['a', 'b', 'c', 'd', 'e'].includes(grade) ? grade : '-';
        } else {
                        // strong 태그가 없는 경우 셀의 텍스트에서 직접 추출
                        const grade = lastCell.textContent.trim().toLowerCase();
                        console.log(`${component} ${spanId} 등급 (direct): ${grade}`);
                        return ['a', 'b', 'c', 'd', 'e'].includes(grade) ? grade : '-';
                    }
                }
            }
        }

        console.log(`${component} ${spanId} 등급을 찾을 수 없음, 기본값 'a' 반환`);
        return '-';
    }

    // 부재별 평균 등급 계산 함수
    function calculateComponentAverages(selectedComponents, spanCount) {
        console.log('부재별 평균 등급 계산 시작');

        const averages = {
            slab: 0, girder: 0, crossbeam: 0, pavement: 0, drainage: 0,
            railing: 0, expansionJoint: 0, bearing: 0, abutment: 0, pier: 0, foundation: 0
        };

        const gradeToNumber = (grade) => {
            const gradeMap = { 'a': 0.1, 'b': 0.2, 'c': 0.4, 'd': 0.7, 'e': 1.0 };
            return gradeMap[grade.toLowerCase()] || null;
        };

    // 최종 점수 및 등급 업데이트 함수
    function updateFinalScoreAndGrade() {
        const tableElement = document.getElementById('totalEvaluationTable');
        if (!tableElement) return;

        // 가중평균 행에서 모든 가중평균 값들을 수집
        const allRows = tableElement.querySelectorAll('tr');
        let weightedRow = null;

        for (let row of allRows) {
            const firstCell = row.querySelector('td[colspan="2"]');
            if (firstCell && (firstCell.textContent.includes('가중치') && firstCell.textContent.includes('평균'))) {
                weightedRow = row;
                break;
            }
        }

        if (!weightedRow) {
            console.log('가중평균 행을 찾을 수 없음');
            return;
        }

        const cells = weightedRow.getElementsByTagName('td');
        let totalWeightedScore = 0;
        let count = 0;

        // 1번째 셀부터 마지막에서 두 번째까지 (염화물 제외)
        // 첫 번째 셀은 colspan="2"이므로 1번째 인덱스부터 시작
        for (let i = 1; i < cells.length - 2; i++) {
            const cellText = cells[i].textContent.trim();
            const value = parseFloat(cellText);

            console.log(`셀 ${i}: ${cellText} -> ${value}`);

            if (!isNaN(value) && value > 0) {
                totalWeightedScore += value;
                count++;
            }
        }

        const finalScore = count > 0 ? totalWeightedScore : 0;
        console.log(`최종 점수 계산: 총합=${totalWeightedScore}, 개수=${count}, 최종=${finalScore}`);

        // 최종 등급 결정
        let finalGrade = 'a';
        if (finalScore >= 1.0) finalGrade = 'e';
        else if (finalScore >= 0.7) finalGrade = 'd';
        else if (finalScore >= 0.4) finalGrade = 'c';
        else if (finalScore >= 0.2) finalGrade = 'b';
        else finalGrade = 'a';

        console.log('최종 등급:', finalGrade);

        // 최종 결과 행 업데이트
        const finalRows = [...allRows].filter(row => {
            const cells = row.getElementsByTagName('td');
            return cells.length >= 2 &&
                   (cells[0].textContent.includes('환산') || cells[0].textContent.includes('상태평가'));
        });

        if (finalRows.length >= 2) {
            // 환산 결함도 점수 행
            const scoreRow = finalRows[0];
            const scoreCells = scoreRow.getElementsByTagName('td');
            if (scoreCells.length >= 2) {
                scoreCells[1].innerHTML = `<strong>${finalScore.safeToFixed(3)}</strong>`;
            }

            // 상태평가 결과 행
            const gradeRow = finalRows[1];
            const gradeCells = gradeRow.getElementsByTagName('td');
            if (gradeCells.length >= 2) {
                gradeCells[1].innerHTML = `<strong>${finalGrade.toUpperCase()}</strong>`;
            }

            console.log('최종 결과 업데이트 완료');
        } else {
            console.log('최종 결과 행을 찾을 수 없음');
        }
    }

        // 각 부재별로 평균 계산
        Object.keys(averages).forEach(component => {
            if (!selectedComponents[component]) {
                averages[component] = 0;
                return;
            }

            let sum = 0;
            let count = 0;

            if (component === 'slab' || component === 'girder' || component === 'crossbeam' ||
                component === 'pavement' || component === 'drainage' || component === 'railing') {
                // 경간(S1, S2, ...) 기준 부재들
                for (let i = 1; i <= spanCount; i++) {
                    const grade = getComponentGradeBySpan(component, `S${i}`);
                    sum += gradeToNumber(grade);
                    count++;
                }
            } else if (component === 'expansionJoint') {
                // 신축이음은 실제 존재하는 위치만 계산
                const expansionPositions = $('#expansionJointPositions').val();
                let expansionLocations = [];

                if (expansionPositions && expansionPositions.trim()) {
                    expansionLocations = expansionPositions.split(',').map(loc => loc.trim().toUpperCase()).filter(loc => loc);
                } else {
                    // 기본값으로 A1, A2 사용
                    expansionLocations = ['A1', 'A2'];
                }

                expansionLocations.forEach(location => {
                    const grade = getComponentGradeBySpan(component, location);
                    if (grade !== '-') {
                        sum += gradeToNumber(grade);
                        count++;
                    }
                });

                console.log(`신축이음 계산 위치: ${expansionLocations.join(', ')}, 평균: ${count > 0 ? (sum/count).safeToFixed(3) : '0.000'}`);
            } else if (component === 'foundation') {
                // 기초는 노출된 기초 위치만 계산
                const exposedPositions = $('#exposedFoundationPositions').val();
                let foundationLocations = [];

                if (exposedPositions && exposedPositions.trim()) {
                    foundationLocations = exposedPositions.split(',').map(pos => pos.trim().toUpperCase()).filter(pos => pos);
                } else {
                    // 기본값으로 교대/교각 모든 위치 사용
                    foundationLocations = ['A1'];
                    for (let i = 1; i < spanCount; i++) {
                        foundationLocations.push(`P${i}`);
                    }
                    foundationLocations.push('A2');
                }

                foundationLocations.forEach(location => {
                    const grade = getComponentGradeBySpan(component, location);
                    if (grade !== '-') {
                        sum += gradeToNumber(grade);
                        count++;
                    }
                });

                console.log(`기초 계산 위치: ${foundationLocations.join(', ')}, 평균: ${count > 0 ? (sum/count).safeToFixed(3) : '0.000'}`);
            } else if (component === 'bearing' || component === 'abutment') {
                // 교량받침과 교대는 교대/교각 모든 위치 계산
                // A1
                const a1Grade = getComponentGradeBySpan(component, 'A1');
                if (a1Grade !== '-') {
                    sum += gradeToNumber(a1Grade);
                    count++;
                }

                // P1 ~ Pn-1
                for (let i = 1; i < spanCount; i++) {
                    const pGrade = getComponentGradeBySpan(component, `P${i}`);
                    if (pGrade !== '-') {
                        sum += gradeToNumber(pGrade);
                        count++;
                    }
                }

                // A2
                const a2Grade = getComponentGradeBySpan(component, 'A2');
                if (a2Grade !== '-') {
                    sum += gradeToNumber(a2Grade);
                    count++;
                }
            } else if (component === 'pier') {
                // 교각만 (P1, P2, ...)
                for (let i = 1; i < spanCount; i++) {
                    const pGrade = getComponentGradeBySpan(component, `P${i}`);
                    if (pGrade !== '-') {
                        sum += gradeToNumber(pGrade);
                        count++;
                    }
                }
            }

            averages[component] = count > 0 ? (sum / count) : 0;
            console.log(`${component} 평균: ${averages[component].safeToFixed(3)} (총 ${count}개)`);
        });

        return averages;
    }

    // 가중합 계산 함수
    function calculateWeightedSum(averages, weights, selectedComponents) {
        let weightedSum = 0;

        Object.keys(averages).forEach(component => {
            if (selectedComponents[component] && weights[component]) {
                weightedSum += averages[component] * weights[component];
            }
        });

        // 내구성 요소 (탄산화) 추가
        weightedSum += 0.1 * weights.carbonation_upper;
        weightedSum += 0.1 * weights.carbonation_lower;

        return weightedSum;
    }

    // 총 가중치 계산 함수
    function calculateTotalWeight(weights, selectedComponents) {
        let totalWeight = 0;

        Object.keys(selectedComponents).forEach(component => {
            if (selectedComponents[component] && weights[component]) {
                totalWeight += weights[component];
            }
        });

        // 내구성 요소 가중치 추가
        totalWeight += weights.carbonation_upper + weights.carbonation_lower;

        return totalWeight;
    }

    // 점수를 등급으로 변환하는 함수
    function convertScoreToGrade(score) {
        if (score <= 0.15) return 'A';
        if (score <= 0.25) return 'B';
        if (score <= 0.40) return 'C';
        if (score <= 0.60) return 'D';
        return 'E';
    }

    // 부재별 등급 가져오기 함수 (기존 함수 유지)
    function getComponentGrade(component) {
        const tableElement = document.getElementById(`${component}EvaluationTable`);
        if (!tableElement) return 'a';

        const rows = tableElement.getElementsByTagName('tbody')[0]?.getElementsByTagName('tr');
        if (!rows || rows.length === 0) return 'a';

        // 모든 행의 등급을 수집
        let grades = [];
        for (let i = 0; i < rows.length; i++) {
            const cells = rows[i].cells;
            if (cells.length > 0) {
                const lastCell = cells[cells.length - 1];
                const gradeText = lastCell.textContent.trim();
                if (gradeText && ['a', 'b', 'c', 'd', 'e'].includes(gradeText)) {
                    grades.push(gradeText);
                }
            }
        }

        // 가장 높은 등급 반환
        if (grades.length === 0) return 'a';

        const gradeOrder = ['a', 'b', 'c', 'd', 'e'];
        let highestGrade = 'a';
        grades.forEach(grade => {
            if (gradeOrder.indexOf(grade) > gradeOrder.indexOf(highestGrade)) {
                highestGrade = grade;
            }
        });

        return highestGrade;
    }

    // 통합 상태평가가 보이는 경우 업데이트
    function updateTotalEvaluationTableIfVisible() {
        const totalEvaluationCard = document.getElementById('totalEvaluationCard');
        if (totalEvaluationCard && totalEvaluationCard.style.display !== 'none') {
            console.log('통합 상태평가 자동 업데이트 시작');

            // 선택된 부재 확인
            const selectedComponents = {
                slab: $('#slabCheck').is(':checked'),
                girder: $('#girderCheck').is(':checked'),
                crossbeam: $('#crossbeamCheck').is(':checked'),
                abutment: $('#abutmentCheck').is(':checked'),
                pier: $('#pierCheck').is(':checked'),
                foundation: $('#foundationCheck').is(':checked'),
                bearing: $('#bearingCheck').is(':checked'),
                expansionJoint: $('#expansionJointCheck').is(':checked'),
                pavement: $('#pavementCheck').is(':checked'),
                drainage: $('#drainageCheck').is(':checked'),
                railing: $('#railingCheck').is(':checked'),
                carbonationUpper: $('#carbonationUpperCheck').is(':checked'),
                carbonationLower: $('#carbonationLowerCheck').is(':checked')
                };

            // 통합 테이블 재생성
            generateTotalEvaluationTable(selectedComponents);
        }
    }

    // 전체 등급 계산
    function calculateOverallRating(grades) {
        const validGrades = grades.filter(grade => ['a', 'b', 'c', 'd', 'e'].includes(grade));
        if (validGrades.length === 0) return 'a';

        const gradeOrder = ['a', 'b', 'c', 'd', 'e'];
        let highestGrade = 'a';
        validGrades.forEach(grade => {
            if (gradeOrder.indexOf(grade) > gradeOrder.indexOf(highestGrade)) {
                highestGrade = grade;
            }
        });

        return highestGrade;
    }

    // 교량받침 상태평가 데이터 행 생성
    function generateBearingTableRow(spanId, bodyCondition, crackWidth, sectionDamage, result) {
        return `
            <tr>
                <td>${spanId}</td>
                <td colspan="2">${bodyCondition || '-'}</td>
                <td>${crackWidth || '-'}</td>
                <td>${sectionDamage || '-'}</td>
                <td>${result || '-'}</td>
            </tr>
        `;
    }

    // 교량받침 상태평가 테이블 생성 함수 예시 (경간수에 따라 자동 생성)
    function generateBearingEvaluationTable(spanCount) {
        let tableHtml = generateBearingTableHeader();
        tableHtml += '<tbody>';
        tableHtml += generateBearingTableRow('A1', '부식', 'b', '-', 'a', 'b');
        for (let i = 1; i < spanCount; i++) {
            tableHtml += generateBearingTableRow(`P${i}`, '도장탈락', 'b', '-', 'a', 'b');
        }
        tableHtml += generateBearingTableRow('A2', '부식', 'b', '-', 'a', 'b');
        tableHtml += '</tbody>';
        return tableHtml;
    }

    // 신축이음 상태평가 데이터 행 생성 (이미지 구조와 동일)
    function generateExpansionJointTableRow(spanId, bodyCondition, footerCrack, footerCrackGrade, sectionDamage, sectionDamageGrade, result) {
        return `
            <tr>
                <td>${spanId}</td>
                <td colspan="1">${bodyCondition || '-'}</td>
                <td>${footerCrack || '-'}</td>
                <td>${footerCrackGrade || 'a'}</td>
                <td>${sectionDamage || '-'}</td>
                <td>${sectionDamageGrade || 'a'}</td>
                <td><strong>${result || 'a'}</strong></td>
            </tr>
        `;
    }

    // 신축이음 상태평가 테이블 생성 함수 예시 (A1, A2만 생성)
    function generateExpansionJointEvaluationTable() {
        let tableHtml = generateExpansionJointTableHeader();
        tableHtml += '<tbody>';
        // 신축이음 위치를 쉼표로 분리하여 배열로 변환
        let locations = [];
        if (bridgeData.expansionJointLocations) {
            locations = bridgeData.expansionJointLocations.split(',').map(loc => loc.trim()).filter(loc => loc);
        }
        // 위치별로 행 생성
        if (locations.length > 0) {
            locations.forEach((loc, idx) => {
                // 샘플 데이터로 생성 (실제 데이터 연동 시 수정)
                tableHtml += generateExpansionJointTableRow(loc, '본체 부식', '균열', 'b', '단면손상', 'b', 'c');
            });
        } else {
            // 위치 정보가 없으면 기본 1행 생성
            tableHtml += generateExpansionJointTableRow('-', '-', '-', 'a', '-', 'a', 'a');
        }
        tableHtml += '</tbody>';
        return tableHtml;
    }

    function generateDrainageTableRow(spanId, damageStatus, result) {
        return `
            <tr>
                <td>${spanId}</td>
                <td>${damageStatus || '-'}</td>
                <td><strong>${result || 'a'}</strong></td>
            </tr>
        `;
    }

    // 등급 평가 함수 개선 - 2줄 데이터 처리 포함
    // evaluation_table_evaluateGrade.js의 evaluateGrade 함수를 사용
    function evaluateGrade(value, damageType = 'crack_width') {
        console.log(`evaluateGrade 호출 - value: ${value}, damageType: ${damageType}`);

        if (value === '-' || value === null || value === undefined || value === 0 || value === '0' || value === '0.00') {
            return 'a';
        }

        let numValue;

        // 2줄 데이터인 경우 처리 (HTML <br> 태그가 포함된 경우)
        if (typeof value === 'string' && value.includes('<br>')) {
            console.log(`2줄 데이터 감지: ${value}`);
            const lines = value.split('<br>');
            if (lines.length >= 2) {
                // 두 번째 줄(계산된 값)을 사용
                numValue = parseFloat(lines[1]);
                console.log(`2번째 줄 값 사용: ${lines[1]} -> ${numValue}`);
            } else {
                numValue = parseFloat(lines[0]);
            }
        } else {
            numValue = parseFloat(value);
        }

        // NaN 처리 추가
        if (isNaN(numValue)) {
            console.log(`NaN 값으로 'a' 등급 반환`);
            return 'a';
        }

        console.log(`평가할 숫자값: ${numValue}`);

        // evaluation_table_evaluateGrade.js의 evaluateGrade 함수 사용
        if (typeof window.evaluateGrade === 'function') {
            const grade = window.evaluateGrade(numValue, damageType);
            console.log(`전문 평가 함수 결과: ${grade}`);
            return grade;
        }

        // 기본 균열폭 기준 (fallback)
        let grade;
        if (numValue >= 1.0) {
            grade = 'e';
        } else if (numValue >= 0.5) {
            grade = 'd';
        } else if (numValue >= 0.3) {
            grade = 'c';
        } else if (numValue >= 0.1) {
            grade = 'b';
        } else {
            grade = 'a';
        }

        console.log(`기본 평가 함수 결과: ${grade}`);
        return grade;
    }

    // 강바닥판 계산 업데이트 (STEEL 타입)
    function updateSteelSlabCalculations($row, $cells, newArea) {
        // 강바닥판 테이블 구조: 경간, 점검면적, 부재균열, 등급, 변형파단, 등급, 연결볼트이완탈락, 등급, 용접연결부결함, 등급, 표면열화면적율, 등급, 최종등급

        // 각 데이터 셀에서 원본 손상물량 추출
        const memberCrackData = extractOriginalDamageValue($cells.eq(2)); // 부재 균열 셀
        const deformationData = extractOriginalDamageValue($cells.eq(4)); // 변형, 파단 셀
        const boltData = extractOriginalDamageValue($cells.eq(6)); // 연결 볼트 이완, 탈락 셀
        const weldData = extractOriginalDamageValue($cells.eq(8)); // 용접연결부 결함 셀
        const surfaceData = extractOriginalDamageValue($cells.eq(10)); // 표면열화 면적율 셀

        console.log(`강바닥판 손상물량 추출:`, {memberCrackData, deformationData, boltData, weldData, surfaceData});

        // 부재 균열 면적율 계산 및 업데이트
        if (memberCrackData.hasData) {
            const newRatio = calculateAreaRatio(memberCrackData.value, newArea);
            $cells.eq(2).text(newRatio > 0 ? newRatio.safeToFixed(2) : '-').attr('data-original-value', memberCrackData.value);
            $cells.eq(3).text(evaluateGrade(newRatio, 'crack_ratio'));
            console.log(`강바닥판 부재 균열 면적율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }

        // 변형, 파단 면적율 계산 및 업데이트
        if (deformationData.hasData) {
            const newRatio = calculateAreaRatio(deformationData.value, newArea);
            calculateCurbArea($cells.eq(4), newRatio, deformationData.value);
            $cells.eq(5).text(evaluateGrade(newRatio, 'deformation_ratio'));
            console.log(`강바닥판 변형, 파단 면적율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }

        // 연결 볼트 이완, 탈락 면적율 계산 및 업데이트
        if (boltData.hasData) {
            const newRatio = calculateAreaRatio(boltData.value, newArea);
            calculateCurbArea($cells.eq(6), newRatio, boltData.value);
            $cells.eq(7).text(evaluateGrade(newRatio, 'bolt_ratio'));
            console.log(`강바닥판 연결 볼트 이완, 탈락 면적율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }

        // 용접연결부 결함 면적율 계산 및 업데이트
        if (weldData.hasData) {
            const newRatio = calculateAreaRatio(weldData.value, newArea);
            calculateCurbArea($cells.eq(8), newRatio, weldData.value);
            $cells.eq(9).text(evaluateGrade(newRatio, 'weld_ratio'));
            console.log(`강바닥판 용접연결부 결함 면적율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }

        // 표면열화 면적율 계산 및 업데이트
        if (surfaceData.hasData) {
            const newRatio = calculateAreaRatio(surfaceData.value, newArea);
            calculateCurbArea($cells.eq(10), newRatio, surfaceData.value);
            $cells.eq(11).text(evaluateGrade(newRatio, 'surface_damage_ratio'));
            console.log(`강바닥판 표면열화 면적율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }
    }

    // 바닥판/거더 계산 업데이트
    function updateSlabGirderCalculations($row, $cells, newArea) {
        // 바닥판/거더 테이블 구조:
        // 경간, 점검면적, 1방향균열폭, 등급, 1방향균열율, 등급, 2방향균열폭, 등급, 2방향균열율, 등급, 누수면적율, 등급, 표면손상면적율, 등급, 철근부식면적율, 등급, 최종등급

        // 각 데이터 셀에서 원본 손상물량 추출
        const crackData1d = extractOriginalDamageValue($cells.eq(4)); // 1방향 균열율 셀
        const crackData2d = extractOriginalDamageValue($cells.eq(8)); // 2방향 균열율 셀
        const leakData = extractOriginalDamageValue($cells.eq(10)); // 누수 면적율 셀
        const surfaceData = extractOriginalDamageValue($cells.eq(12)); // 표면손상 면적율 셀
        const rebarData = extractOriginalDamageValue($cells.eq(14)); // 철근부식 면적율 셀

        console.log(`손상물량 추출 완료:`, {crackData1d, crackData2d, leakData, surfaceData, rebarData});

        // 1방향 균열율 계산 및 업데이트
        if (crackData1d.hasData) {
            const newRatio = calculateCrackRatio(crackData1d.value, newArea);
            $cells.eq(4).text(newRatio > 0 ? newRatio.safeToFixed(2) : '-').attr('data-original-value', crackData1d.value);
            $cells.eq(5).text(evaluateGrade(newRatio, 'crack_ratio'));
            console.log(`1방향 균열율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }

        // 2방향 균열율 계산 및 업데이트
        if (crackData2d.hasData) {
            const newRatio = calculateAreaRatio(crackData2d.value, newArea);
            $cells.eq(8).text(newRatio > 0 ? newRatio.safeToFixed(2) : '-').attr('data-original-value', crackData2d.value);
            $cells.eq(9).text(evaluateGrade(newRatio, 'crack_ratio'));
            console.log(`2방향 균열율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }

        // 누수 면적율 계산 및 업데이트
        if (leakData.hasData) {
            const newRatio = calculateAreaRatio(leakData.value, newArea);
            calculateCurbArea($cells.eq(10), newRatio, leakData.value);
            $cells.eq(11).text(evaluateGrade(newRatio, 'leak_ratio'));
            console.log(`누수 면적율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }

        // 표면손상 면적율 계산 및 업데이트
        if (surfaceData.hasData) {
            const newRatio = calculateAreaRatio(surfaceData.value, newArea);
            calculateCurbArea($cells.eq(12), newRatio, surfaceData.value);
            $cells.eq(13).text(evaluateGrade(newRatio, 'surface_damage_ratio'));
            console.log(`표면손상 면적율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }

        // 철근부식 면적율 계산 및 업데이트
        if (rebarData.hasData) {
            const newRatio = calculateAreaRatio(rebarData.value, newArea);
            calculateCurbArea($cells.eq(14), newRatio, rebarData.value);
            $cells.eq(15).text(evaluateGrade(newRatio, 'rebar_corrosion_ratio'));
            console.log(`철근부식 면적율 업데이트: ${newRatio.safeToFixed(2)}%`);
        }
    }

    // 탄산화 시험 위치 입력 변경 이벤트
    $('#carbonationUpperPositions, #carbonationLowerPositions').on('input', function() {
        console.log('탄산화 시험 위치 입력 변경됨:', $(this).val());
        // 통합산정결과표가 표시되어 있다면 다시 생성
        const totalEvaluationTable = document.getElementById('totalEvaluationTable');
        if (totalEvaluationTable && totalEvaluationTable.innerHTML.trim() !== '') {
            console.log('통합산정결과표 재생성 시작');
            // 선택된 부재 정보 가져오기
            const selectedComponents = {
                slab: $('#slabCheck').is(':checked'),
                girder: $('#girderCheck').is(':checked'),
                crossbeam: $('#crossbeamCheck').is(':checked'),
                abutment: $('#abutmentCheck').is(':checked'),
                pier: $('#pierCheck').is(':checked'),
                foundation: $('#foundationCheck').is(':checked'),
                bearing: $('#bearingCheck').is(':checked'),
                expansionJoint: $('#expansionJointCheck').is(':checked'),
                pavement: $('#pavementCheck').is(':checked'),
                drainage: $('#drainageCheck').is(':checked'),
                railing: $('#railingCheck').is(':checked'),
                carbonationUpper: $('#carbonationUpperCheck').is(':checked'),
                carbonationLower: $('#carbonationLowerCheck').is(':checked')
            };

            console.log('선택된 부재:', selectedComponents);

            // 통합산정결과표 다시 생성
            generateTotalEvaluationTable(selectedComponents);
        } else {
            console.log('통합산정결과표가 표시되지 않음');
        }
    });

    // 탄산화 시험 체크박스 변경 이벤트
    $('#carbonationUpperCheck, #carbonationLowerCheck').on('change', function() {
        console.log('탄산화 시험 체크박스 변경됨:', $(this).attr('id'), $(this).is(':checked'));
        // 통합산정결과표가 표시되어 있다면 다시 생성
        const totalEvaluationTable = document.getElementById('totalEvaluationTable');
        if (totalEvaluationTable && totalEvaluationTable.innerHTML.trim() !== '') {
            console.log('통합산정결과표 재생성 시작');
            // 선택된 부재 정보 가져오기
            const selectedComponents = {
                slab: $('#slabCheck').is(':checked'),
                girder: $('#girderCheck').is(':checked'),
                crossbeam: $('#crossbeamCheck').is(':checked'),
                abutment: $('#abutmentCheck').is(':checked'),
                pier: $('#pierCheck').is(':checked'),
                foundation: $('#foundationCheck').is(':checked'),
                bearing: $('#bearingCheck').is(':checked'),
                expansionJoint: $('#expansionJointCheck').is(':checked'),
                pavement: $('#pavementCheck').is(':checked'),
                drainage: $('#drainageCheck').is(':checked'),
                railing: $('#railingCheck').is(':checked'),
                carbonationUpper: $('#carbonationUpperCheck').is(':checked'),
                carbonationLower: $('#carbonationLowerCheck').is(':checked')
            };

            console.log('선택된 부재:', selectedComponents);

            // 통합산정결과표 다시 생성
            generateTotalEvaluationTable(selectedComponents);
        } else {
            console.log('통합산정결과표가 표시되지 않음');
        }
    });

    // 페이지 로드 시 고정 부재명 초기화 함수
    function initializeStickyHeader() {
        console.log('페이지 로드 시 고정 부재명 초기화 시작');

        // 현재 체크박스 상태에 따라 고정 부재명 업데이트
        const selectedComponents = {
            slab: $('#slabCheck').is(':checked'),
            girder: $('#girderCheck').is(':checked'),
            crossbeam: $('#crossbeamCheck').is(':checked'),
            abutment: $('#abutmentCheck').is(':checked'),
            pier: $('#pierCheck').is(':checked'),
            foundation: $('#foundationCheck').is(':checked'),
            bearing: $('#bearingCheck').is(':checked'),
            expansionJoint: $('#expansionJointCheck').is(':checked'),
            pavement: $('#pavementCheck').is(':checked'),
            drainage: $('#drainageCheck').is(':checked'),
            railing: $('#railingCheck').is(':checked'),
            carbonationUpper: $('#carbonationUpperCheck').is(':checked'),
            carbonationLower: $('#carbonationLowerCheck').is(':checked')
        };

        console.log('초기 체크박스 상태:', selectedComponents);
        updateStickyHeader(selectedComponents);
    }

    // 고정 부재명 업데이트 함수
    function updateStickyHeader(selectedComponents) {
        console.log('고정 부재명 업데이트 시작:', selectedComponents);

        const stickyHeader = document.querySelector('.sticky-header');
        if (!stickyHeader) {
            console.log('고정 헤더를 찾을 수 없습니다.');
            return;
        }

        // 부재명과 체크박스 ID 매핑
        const componentMapping = {
            'slab': { name: '바닥판', href: '#slabEvaluationHeader' },
            'girder': { name: '거더', href: '#girderEvaluationHeader' },
            'crossbeam': { name: '가로보', href: '#crossbeamEvaluationHeader' },
            'abutment': { name: '교대', href: '#abutmentEvaluationHeader' },
            'pier': { name: '교각', href: '#pierEvaluationHeader' },
            'foundation': { name: '기초', href: '#foundationEvaluationHeader' },
            'bearing': { name: '교량받침', href: '#bearingEvaluationHeader' },
            'expansionJoint': { name: '신축이음', href: '#expansionJointEvaluationHeader' },
            'pavement': { name: '교면포장', href: '#pavementEvaluationHeader' },
            'drainage': { name: '배수시설', href: '#drainageEvaluationHeader' },
            'railing': { name: '난간 및 연석', href: '#railingEvaluationHeader' }
        };

        // 기존 부재명 버튼들 제거 (통합산정결과표 버튼은 유지)
        const existingButtons = stickyHeader.querySelectorAll('a[href^="#"]:not([href="#totalEvaluationHeader"])');
        existingButtons.forEach(button => button.remove());

        // 선택된 부재에 대해서만 버튼 생성
        Object.keys(componentMapping).forEach(componentKey => {
            if (selectedComponents[componentKey]) {
                const component = componentMapping[componentKey];
                const button = document.createElement('a');
                button.href = component.href;
                button.className = 'btn btn-sm';
                button.style.cssText = 'background-color: rgb(55, 144, 245); color: #fff; border: none; margin-right: 5px;';
                button.textContent = component.name;

                // 통합산정결과표 버튼 앞에 삽입
                const totalButton = stickyHeader.querySelector('a[href="#totalEvaluationHeader"]');
                if (totalButton) {
                    stickyHeader.insertBefore(button, totalButton);
                } else {
                    stickyHeader.appendChild(button);
                }
            }
        });

        console.log('고정 부재명 업데이트 완료');
    }

    // 탄산화 시험 기능 테스트 함수
    function testCarbonationFunction() {
        console.log('=== 탄산화 시험 기능 테스트 ===');
        console.log('탄산화 상부 체크박스:', $('#carbonationUpperCheck').is(':checked'));
        console.log('탄산화 하부 체크박스:', $('#carbonationLowerCheck').is(':checked'));
        console.log('탄산화 상부 위치:', $('#carbonationUpperPositions').val());
        console.log('탄산화 하부 위치:', $('#carbonationLowerPositions').val());

        const totalEvaluationTable = document.getElementById('totalEvaluationTable');
        if (totalEvaluationTable) {
            console.log('통합산정결과표 존재:', totalEvaluationTable.innerHTML.length > 0);
            const carbonationDropdowns = totalEvaluationTable.querySelectorAll('.carbonation-grade');
            console.log('탄산화 드롭다운 개수:', carbonationDropdowns.length);
        } else {
            console.log('통합산정결과표 없음');
        }
    }

    // 페이지 로드 시 테스트 함수 실행
    $(document).ready(function() {
        // 5초 후에 테스트 함수 실행
        setTimeout(testCarbonationFunction, 5000);
    });

    // 네비게이션 클릭 이벤트 처리
    $(document).on('click', '.sticky-header a[href^="#"]', function(e) {
        e.preventDefault();

        const targetId = $(this).attr('href');
        const targetElement = $(targetId);

        if (targetElement.length > 0) {
            // 모든 네비게이션 버튼에서 active 클래스 제거
            $('.sticky-header a').removeClass('active');

            // 클릭된 버튼에 active 클래스 추가
            $(this).addClass('active');

            // 부드러운 스크롤로 해당 요소로 이동
            $('html, body').animate({
                scrollTop: targetElement.offset().top - 150
            }, 500);

            // 잠시 후 active 클래스 제거 (시각적 피드백)
            setTimeout(() => {
                $(this).removeClass('active');
            }, 1000);

            console.log(`네비게이션 클릭: ${targetId}로 이동`);
        }
    });

    // 스크롤 시 현재 보이는 섹션에 따라 네비게이션 버튼 활성화
    $(window).on('scroll', function() {
        const scrollTop = $(window).scrollTop();
        const windowHeight = $(window).height();

        // 각 부재 섹션의 위치 확인
        const sections = [
            'slabEvaluationHeader',
            'girderEvaluationHeader',
            'crossbeamEvaluationHeader',
            'abutmentEvaluationHeader',
            'pierEvaluationHeader',
            'foundationEvaluationHeader',
            'bearingEvaluationHeader',
            'expansionJointEvaluationHeader',
            'pavementEvaluationHeader',
            'drainageEvaluationHeader',
            'railingEvaluationHeader',
            'totalEvaluationHeader'
        ];

        let activeSection = '';

        sections.forEach(sectionId => {
            const element = $(`#${sectionId}`);
            if (element.length > 0) {
                const elementTop = element.offset().top;
                const elementBottom = elementTop + element.outerHeight();

                // 현재 스크롤 위치가 해당 섹션 내에 있는지 확인
                if (scrollTop + 200 >= elementTop && scrollTop + 200 <= elementBottom) {
                    activeSection = sectionId;
                }
            }
        });

        // 네비게이션 버튼 활성화 상태 업데이트
        $('.sticky-header a').removeClass('active');
        if (activeSection) {
            $(`.sticky-header a[href="#${activeSection}"]`).addClass('active');
        }
    });
});

// 스낵바 메시지 함수 추가
function showSnackMessage(message, type = 'info') {
    // type: 'info', 'success', 'error'
    let color = '#323232';
    if (type === 'success') color = '#28a745';
    if (type === 'error') color = '#dc3545';

    let $snackbar = $('#snackbar-message');
    if ($snackbar.length === 0) {
        $snackbar = $('<div id="snackbar-message"></div>').appendTo('body');
        $snackbar.css({
            'min-width': '200px',
            'background': color,
            'color': '#fff',
            'text-align': 'center',
            'border-radius': '4px',
            'padding': '12px 24px',
            'position': 'fixed',
            'z-index': 9999,
            'left': '50%',
            'bottom': '40px',
            'transform': 'translateX(-50%)',
            'font-size': '1rem',
            'box-shadow': '0 2px 8px rgba(0,0,0,0.2)',
            'display': 'none'
        });
    }
    $snackbar.text(message).css('background', color).fadeIn(200);

    setTimeout(function() {
        $snackbar.fadeOut(400);
    }, 2000);
}

// 탄산화 시험 데이터 저장 함수
function saveCarbonationTestData() {
    console.log('=== 탄산화 시험 데이터 저장 시작 ===');



    // 현재 파일 ID 가져오기 (전역 변수에서)
    const fileId = window.currentFileId || localStorage.getItem('currentFileId');
    if (!fileId) {
        console.error('파일 ID를 찾을 수 없습니다.');
        showSnackMessage('파일 ID를 찾을 수 없습니다.', 'error');
        return;
    }

    // 모든 탄산화 드롭다운에서 데이터 수집
    const carbonationData = [];

    $('.carbonation-grade').each(function() {
        const $dropdown = $(this);
        const selectedValue = $dropdown.val();
        const component = $dropdown.data('component');
        const position = $dropdown.data('position');
        const testType = $dropdown.data('type');

        console.log(`드롭다운 데이터: component=${component}, position=${position}, testType=${testType}, grade=${selectedValue}`);

        // 선택된 값이 있는 경우에만 저장
        if (selectedValue && selectedValue !== '') {
            carbonationData.push({
                component: component,
                position: position,
                test_type: testType,
                grade: selectedValue
            });
        }
    });

    console.log('수집된 탄산화 데이터:', carbonationData);

    if (carbonationData.length === 0) {
        console.log('저장할 탄산화 데이터가 없습니다.');
        showSnackMessage('저장할 탄산화 데이터가 없습니다.', 'info');
        return;
    }

    // 서버로 데이터 전송
    $.ajax({
        url: '/api/save_carbonation_test',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            file_id: fileId,
            carbonation_data: carbonationData
        }),
        success: function(response) {
            console.log('탄산화 데이터 저장 성공:', response);
            if (response.success) {
                showSnackMessage(`${response.saved_count}개의 탄산화 시험 데이터가 저장되었습니다.`, 'success');
            } else {
                showSnackMessage('데이터 저장에 실패했습니다.', 'error');
            }
        },
        error: function(xhr, status, error) {
            console.error('탄산화 데이터 저장 실패:', error);
            console.error('응답:', xhr.responseText);
            showSnackMessage('데이터 저장 중 오류가 발생했습니다.', 'error');
        }
    });
}

// 탄산화 시험 데이터 불러오기 함수
function loadCarbonationTestData() {
    console.log('=== 탄산화 시험 데이터 불러오기 시작 ===');

    const fileId = window.currentFileId || localStorage.getItem('currentFileId');
    if (!fileId) {
        console.log('파일 ID를 찾을 수 없어 탄산화 데이터를 불러올 수 없습니다.');
        return;
    }

    $.ajax({
        url: '/api/get_carbonation_test',
        type: 'GET',
        data: { file_id: fileId },
        success: function(response) {
            console.log('탄산화 데이터 불러오기 성공:', response);
            if (response.success && response.carbonation_data) {
                // 불러온 데이터로 드롭다운 설정
                response.carbonation_data.forEach(function(item) {
                    const selector = `.carbonation-grade[data-component="${item.component}"][data-position="${item.position}"][data-type="${item.test_type}"]`;
                    $(selector).val(item.grade);
                    console.log(`드롭다운 설정: ${selector} = ${item.grade}`);
                });

                // 데이터 불러온 후 통합산정결과표 재계산
                recalculateTotalEvaluationTable();

                if (response.count > 0) {
                    showSnackMessage(`${response.count}개의 탄산화 시험 데이터를 불러왔습니다.`, 'success');
                }
            }
        },
        error: function(xhr, status, error) {
            console.error('탄산화 데이터 불러오기 실패:', error);
            console.error('응답:', xhr.responseText);
        }
    });
}

// 기본 가중치 설정 함수
function setDefaultWeights() {
    const structureType = $('#structureType').val();
    console.log('기본 가중치 설정 - 구조형식:', structureType);

    // evaluation_table_evaluateGrade.js의 STRUCTURE_WEIGHTS 사용
    let weights = {};

    if (typeof STRUCTURE_WEIGHTS !== 'undefined' && STRUCTURE_WEIGHTS[structureType]) {
        const structureWeights = STRUCTURE_WEIGHTS[structureType];

        // 구조형식별 가중치를 입력 필드명에 맞게 매핑
        weights = {
            slab: structureWeights['바닥판'] || structureWeights['슬래브'] || 0,
            girder: structureWeights['거더'] || 0,
            crossbeam: structureWeights['2차부재'] || 0,
            pavement: structureWeights['교면포장'] || 0,
            drainage: structureWeights['배수시설'] || 0,
            railing: structureWeights['난간/연석'] || 0,
            expansionJoint: structureWeights['신축이음'] || 0,
            bearing: structureWeights['교량받침'] || 0,
            abutment: structureWeights['교대/교각'] || 0,
            pier: structureWeights['교대/교각'] || 0,
            foundation: structureWeights['기초'] || 0,
            carbonation_upper: structureWeights['탄산화_상부'] || 0,
            carbonation_lower: structureWeights['탄산화_하부'] || 0
        };

        console.log('구조형식별 가중치 적용:', weights);
    } else {
        // 구조형식이 없거나 매칭되지 않는 경우 - 모든 가중치를 0으로 설정
        weights = {
            slab: 0,
            girder: 0,
            crossbeam: 0,
            pavement: 0,
            drainage: 0,
            railing: 0,
            expansionJoint: 0,
            bearing: 0,
            abutment: 0,
            pier: 0,
            foundation: 0,
            carbonation_upper: 0,
            carbonation_lower: 0
        };

        console.log('구조형식 매칭 없음 - 모든 가중치를 0으로 설정:', weights);
    }

    // 가중치 입력 필드에 값 설정
    $('#weightSlab').val(weights.slab);
    $('#weightGirder').val(weights.girder);
    $('#weightCrossbeam').val(weights.crossbeam);
    $('#weightPavement').val(weights.pavement);
    $('#weightDrainage').val(weights.drainage);
    $('#weightRailing').val(weights.railing);
    $('#weightExpansionJoint').val(weights.expansionJoint);
    $('#weightBearing').val(weights.bearing);
    $('#weightAbutment').val(weights.abutment);
    $('#weightPier').val(weights.pier);
    $('#weightFoundation').val(weights.foundation);
    $('#weightCarbonationUpper').val(weights.carbonation_upper);
    $('#weightCarbonationLower').val(weights.carbonation_lower);

    console.log('가중치 설정 완료:', weights);
}

// 부재 선택 데이터 저장 함수
function saveComponentSelection() {
    console.log('=== 부재 선택 데이터 저장 시작 ===');

    const fileId = window.currentFileId || window.currentSelectedFilename || localStorage.getItem('currentFileId');
    if (!fileId) {
        console.error('파일 ID를 찾을 수 없습니다.');
        showSnackMessage('파일 ID를 찾을 수 없습니다.', 'error');
        return;
    }

    // 현재 선택된 부재들 수집
    const selectedComponents = {};

    // 각 부재 체크박스 상태 확인 (명시적으로 true/false 저장)
    selectedComponents.slab = $('#slabCheck').is(':checked');
    selectedComponents.girder = $('#girderCheck').is(':checked');
    selectedComponents.crossbeam = $('#crossbeamCheck').is(':checked');
    selectedComponents.abutment = $('#abutmentCheck').is(':checked');
    selectedComponents.pier = $('#pierCheck').is(':checked');
    selectedComponents.foundation = $('#foundationCheck').is(':checked');
    selectedComponents.bearing = $('#bearingCheck').is(':checked');
    selectedComponents.expansionJoint = $('#expansionJointCheck').is(':checked');
    selectedComponents.pavement = $('#pavementCheck').is(':checked');
    selectedComponents.drainage = $('#drainageCheck').is(':checked');
    selectedComponents.railing = $('#railingCheck').is(':checked');
    selectedComponents.carbonationUpper = $('#carbonationUpperCheck').is(':checked');
    selectedComponents.carbonationLower = $('#carbonationLowerCheck').is(':checked');

    console.log('현재 체크박스 상태:', selectedComponents);

    // 교량 정보 수집
    const bridgeInfo = {
        bridgeName: $('#bridgeName').val() || '',
        structureType: $('#structureType').val() || '',
        spanCount: parseInt($('#spanCount').val()) || 0,
        slabType: $('#slabType').val() || '',
        girderType: $('#girderType').val() || '',
        crossbeamType: $('#crossbeamType').val() || '',
        pavementType: $('#pavementType').val() || '',
        exposedFoundationPositions: $('#exposedFoundationPositions').val() || '',
        expansionJointPositions: $('#expansionJointPositions').val() || '',
        carbonationUpperPositions: $('#carbonationUpperPositions').val() || '',
        carbonationLowerPositions: $('#carbonationLowerPositions').val() || '',
        chlorideUpperPositions: $('#chlorideUpperPositions').val() || '',
        chlorideLowerPositions: $('#chlorideLowerPositions').val() || ''
    };

    console.log('저장할 부재 선택 데이터:', selectedComponents);
    console.log('저장할 교량 정보:', bridgeInfo);

    // 서버로 데이터 전송
    $.ajax({
        url: '/api/save_component_selection',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            file_id: fileId,
            selected_components: selectedComponents,
            bridge_info: bridgeInfo
        }),
        success: function(response) {
            console.log('부재 선택 데이터 저장 성공:', response);
            if (response.success) {
                console.log('저장된 데이터 확인:', {
                    fileId: fileId,
                    selectedComponents: selectedComponents,
                    bridgeInfo: bridgeInfo
                });
                showSnackMessage('부재 선택 및 교량 정보가 저장되었습니다.', 'success');
            } else {
                showSnackMessage('데이터 저장에 실패했습니다.', 'error');
            }
        },
        error: function(xhr, status, error) {
            console.error('부재 선택 데이터 저장 실패:', error);
            console.error('응답:', xhr.responseText);
            showSnackMessage('데이터 저장 중 오류가 발생했습니다.', 'error');
        }
    });
}

// 부재 선택 데이터 불러오기 함수
function loadComponentSelection() {
    console.log('=== 부재 선택 데이터 불러오기 시작 ===');

    const fileId = window.currentFileId || window.currentSelectedFilename || localStorage.getItem('currentFileId');
    if (!fileId) {
        console.log('파일 ID를 찾을 수 없어 부재 선택 데이터를 불러올 수 없습니다.');
        return;
    }

    $.ajax({
        url: '/api/get_component_selection',
        type: 'GET',
        data: { file_id: fileId },
        success: function(response) {
            console.log('부재 선택 데이터 불러오기 성공:', response);
            if (response.success) {
                // 부재 선택 상태 복원
                if (response.selected_components) {
                    console.log('저장된 부재 선택 상태:', response.selected_components);

                    // 부재명과 체크박스 ID 매핑
                    const componentCheckboxMapping = {
                        'slab': '#slabCheck',
                        'girder': '#girderCheck',
                        'crossbeam': '#crossbeamCheck',
                        'abutment': '#abutmentCheck',
                        'pier': '#pierCheck',
                        'foundation': '#foundationCheck',
                        'bearing': '#bearingCheck',
                        'expansionJoint': '#expansionJointCheck',
                        'pavement': '#pavementCheck',
                        'drainage': '#drainageCheck',
                        'railing': '#railingCheck',
                        'carbonationUpper': '#carbonationUpperCheck',
                        'carbonationLower': '#carbonationLowerCheck'
                    };

                    // 모든 체크박스를 명시적으로 처리 (체크 및 해제 모두)
                    Object.keys(componentCheckboxMapping).forEach(function(componentName) {
                        const checkboxId = componentCheckboxMapping[componentName];
                        const isChecked = response.selected_components[componentName] === true;
                        console.log(`${componentName} (${checkboxId}): ${isChecked ? 'checked' : 'unchecked'}`);
                        $(checkboxId).prop('checked', isChecked);
                    });

                    // 체크박스 상태에 따른 관련 입력 필드 표시/숨김
                    if ($('#foundationCheck').is(':checked')) {
                        $('#foundationExposedInput').show();
                    } else {
                        $('#foundationExposedInput').hide();
                        $('#exposedFoundationPositions').val(''); // 해제시 값 초기화
                    }

                    if ($('#expansionJointCheck').is(':checked')) {
                        $('#expansionJointLocationInput').show();
                    } else {
                        $('#expansionJointLocationInput').hide();
                        $('#expansionJointPositions').val(''); // 해제시 값 초기화
                    }

                    console.log('체크박스 상태 복원 및 관련 필드 표시/숨김 처리 완료');

                    // 고정 부재명 업데이트
                   // updateStickyHeader(response.selected_components);
                }

                // 교량 정보 복원
                if (response.bridge_info) {
                    const bridgeInfo = response.bridge_info;
                    $('#bridgeName').val(bridgeInfo.bridgeName || '');
                    $('#structureType').val(bridgeInfo.structureType || '').trigger('change');
                    $('#spanCount').val(bridgeInfo.spanCount || '');
                    $('#slabType').val(bridgeInfo.slabType || '').trigger('change');
                    $('#girderType').val(bridgeInfo.girderType || '').trigger('change');
                    $('#crossbeamType').val(bridgeInfo.crossbeamType || '').trigger('change');
                    $('#pavementType').val(bridgeInfo.pavementType || '').trigger('change');
                    $('#exposedFoundationPositions').val(bridgeInfo.exposedFoundationPositions || '');
                    $('#expansionJointPositions').val(bridgeInfo.expansionJointPositions || '');
                    $('#carbonationUpperPositions').val(bridgeInfo.carbonationUpperPositions || '');
                    $('#carbonationLowerPositions').val(bridgeInfo.carbonationLowerPositions || '');
                    $('#chlorideUpperPositions').val(bridgeInfo.chlorideUpperPositions || '');
                    $('#chlorideLowerPositions').val(bridgeInfo.chlorideLowerPositions || '');
                }

                console.log('부재 선택 및 교량 정보 복원 완료');
            }
        },
        error: function(xhr, status, error) {
            console.error('부재 선택 데이터 불러오기 실패:', error);
            console.error('응답:', xhr.responseText);
        }
    });
}

// 교량 정보 저장 함수
function saveBridgeInfo() {
    console.log('=== 교량 정보 저장 시작 ===');

    const fileId = bridgeData.id;
    if (!fileId) {
        console.error('파일 ID를 찾을 수 없습니다.');
        return;
    }

    const bridgeInfo = {
        bridgeName: $('#bridgeName').val() || '',
        structureType: $('#structureType').val() || '',
        spanCount: parseInt($('#spanCount').val()) || 0,
        slabType: $('#slabType').val() || '',
        girderType: $('#girderType').val() || '',
        crossbeamType: $('#crossbeamType').val() || '',
        pavementType: $('#pavementType').val() || '',
        exposedFoundationPositions: $('#exposedFoundationPositions').val() || '',
        expansionJointPositions: $('#expansionJointPositions').val() || '',
        carbonationUpperPositions: $('#carbonationUpperPositions').val() || '',
        carbonationLowerPositions: $('#carbonationLowerPositions').val() || '',
        chlorideUpperPositions: $('#chlorideUpperPositions').val() || '',
        chlorideLowerPositions: $('#chlorideLowerPositions').val() || ''
    };

    $.ajax({
        url: '/api/save_bridge_info',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            file_id: fileId,
            bridge_info: bridgeInfo
        }),
        success: function(response) {
            console.log('교량 정보 저장 성공:', response);
        },
        error: function(xhr, status, error) {
            console.error('교량 정보 저장 실패:', error);
        }
    });
}

// 교량 정보 및 부재 선택 실시간 저장 이벤트 리스너 추가
$(document).ready(function() {
    // 교량 정보 입력 필드 변경 시 자동 저장
    $('#slabType, #girderType, #crossbeamType, #pavementType, #exposedFoundationPositions, #expansionJointPositions, #carbonationUpperPositions, #carbonationLowerPositions, #chlorideUpperPositions, #chlorideLowerPositions').on('change input', function() {
        // 디바운싱을 위해 타이머 사용
        clearTimeout(window.bridgeInfoSaveTimer);
        window.bridgeInfoSaveTimer = setTimeout(function() {
            saveComponentSelection(); // 교량 정보도 이 함수에서 함께 저장됨
        }, 1000); // 1초 후 저장
    });

    // 교면포장 타입 변경 시 실시간 등급 재계산
    $('#pavementType').on('change', function() {
        console.log('교면포장 타입 변경됨:', $(this).val());
        updatePavementGrades();
    });

    // 교면포장 등급 재계산 함수
    function updatePavementGrades() {
        const pavementTable = document.getElementById('pavementEvaluationTable');
        if (!pavementTable) {
            console.log('교면포장 테이블을 찾을 수 없습니다.');
            return;
        }

        const pavementType = $("#pavementType").val();
        const damageType = pavementType === 'CONCRETE' ? 'damage_ratio_concrete' : 'damage_ratio_asphalt';

        console.log(`교면포장 등급 재계산 - 타입: ${pavementType}, 평가기준: ${damageType}`);

        // 교면포장 테이블의 모든 행에 대해 등급 재계산
        const rows = pavementTable.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 4) {
                // 포장불량 면적율 셀 (3번째 셀, 인덱스 2)
                const damageRatioCell = cells[2];
                const damageRatio = parseFloat(damageRatioCell.textContent) || 0;

                // 등급 셀 (4번째 셀, 인덱스 3)
                const gradeCell = cells[3];
                const newGrade = evaluateGrade(damageRatio, damageType);
                gradeCell.textContent = newGrade;

                console.log(`경간 ${cells[0].textContent}: ${damageRatio}% -> ${newGrade}등급`);
            }
        });

        // 최종 등급도 재계산 - 함수 존재 여부 확인
        rows.forEach(row => {
            if (typeof updateFinalGrade === 'function') {
                updateFinalGrade($(row));
            } else {
                console.warn('updateFinalGrade 함수를 찾을 수 없습니다.');
            }
        });

        // 통합 상태평가 자동 업데이트 - 함수 존재 여부 확인
        if (typeof updateTotalEvaluationTableIfVisible === 'function') {
            updateTotalEvaluationTableIfVisible();
        } else {
            console.warn('updateTotalEvaluationTableIfVisible 함수를 찾을 수 없습니다.');
        }
    }

    // 부재 체크박스 변경 시 자동 저장 및 해당 평가 카드 표시/숨김
    $('#slabCheck, #girderCheck, #crossbeamCheck, #abutmentCheck, #pierCheck, #foundationCheck, #bearingCheck, #expansionJointCheck, #pavementCheck, #drainageCheck, #railingCheck, #carbonationUpperCheck, #carbonationLowerCheck').on('change', function() {
        const checkboxId = $(this).attr('id');
        const isChecked = $(this).is(':checked');
        console.log(`체크박스 변경됨: ${checkboxId} = ${isChecked}`);

        // 체크박스와 평가 카드 매핑
        const cardMapping = {
            'slabCheck': '#slabEvaluationCard',
            'girderCheck': '#girderEvaluationCard',
            'crossbeamCheck': '#crossbeamEvaluationCard',
            'abutmentCheck': '#abutmentEvaluationCard',
            'pierCheck': '#pierEvaluationCard',
            'foundationCheck': '#foundationEvaluationCard',
            'bearingCheck': '#bearingEvaluationCard',
            'expansionJointCheck': '#expansionJointEvaluationCard',
            'pavementCheck': '#pavementEvaluationCard',
            'drainageCheck': '#drainageEvaluationCard',
            'railingCheck': '#railingEvaluationCard'
            // 탄산화는 별도 카드가 없으므로 제외
        };

        // 해당 평가 카드 표시/숨김
        const cardSelector = cardMapping[checkboxId];
        if (cardSelector) {
            if (isChecked) {
                $(cardSelector).show();
            } else {
                $(cardSelector).hide();
            }
        }

        // 현재 선택된 부재들 수집
        const selectedComponents = {
            slab: $('#slabCheck').is(':checked'),
            girder: $('#girderCheck').is(':checked'),
            crossbeam: $('#crossbeamCheck').is(':checked'),
            abutment: $('#abutmentCheck').is(':checked'),
            pier: $('#pierCheck').is(':checked'),
            foundation: $('#foundationCheck').is(':checked'),
            bearing: $('#bearingCheck').is(':checked'),
            expansionJoint: $('#expansionJointCheck').is(':checked'),
            pavement: $('#pavementCheck').is(':checked'),
            drainage: $('#drainageCheck').is(':checked'),
            railing: $('#railingCheck').is(':checked'),
            carbonationUpper: $('#carbonationUpperCheck').is(':checked'),
            carbonationLower: $('#carbonationLowerCheck').is(':checked')
        };

        // 고정 부재명 업데이트
        //updateStickyHeader(selectedComponents);

        clearTimeout(window.componentSelectionSaveTimer);
        window.componentSelectionSaveTimer = setTimeout(function() {
            console.log('체크박스 변경으로 인한 자동 저장 시작');
            saveComponentSelection();
        }, 500); // 0.5초 후 저장
    });
});
