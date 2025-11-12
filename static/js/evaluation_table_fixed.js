$(document).ready(function() {
    // 전역 변수 정의
    let bridgeData = {
        name: '',
        structureType: '',
        length: 0,
        width: 0,
        spanCount: 0,
        expansionJointLocations: '',
        spans: []
    };

    let damageData = {
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

    // 저장된 교량 데이터 배열
    let savedBridges = [];

    // 디버그 로그
    console.log("교량 상태평가표 스크립트 로드됨");

    // 페이지 로드 시 저장된 데이터 불러오기
    function loadSavedBridges() {
        try {
            const savedData = localStorage.getItem('savedBridges');
            if (savedData) {
                savedBridges = JSON.parse(savedData);
                console.log('저장된 교량 데이터 로드 완료:', savedBridges);
            }
        } catch (error) {
            console.error('저장된 교량 데이터 로드 중 오류 발생:', error);
            savedBridges = [];
        }
    }

    // 초기화 함수
    function initialize() {
        // 저장된 데이터 로드
        loadSavedBridges();
        // 교량 리스트 업데이트
        updateBridgeList();
        // 교량명 드롭다운 초기화
        initializeBridgeNameDropdown();
    }

    // 페이지 로드 시 초기화 실행
    initialize();

    // 면적 입력 이벤트 리스너 추가
    addAreaInputListeners();

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

        // 교량 선택 이벤트 리스너
        bridgeNameSelect.addEventListener('change', function() {
            const selectedFilename = this.value;
            console.log('교량 선택됨:', selectedFilename);
            if (selectedFilename) {
                // 선택된 파일명을 전역 변수로 저장
                window.currentSelectedFilename = selectedFilename;
                loadBridgeData(selectedFilename);
            } else {
                // 선택 해제시 폼 초기화
                resetForm();
            }
        });
    }

    function loadBridgeData(filename) {
        console.log('교량 데이터 로드 시작:', filename);
        $.ajax({
            url: `/api/bridge_data/${filename}`,
            method: 'GET',
            success: function(response) {
                console.log('교량 데이터 로드 성공:', response);
                if (response.success) {
                    const data = response.data;

                    // 기본 정보 채우기
                    document.getElementById('id').value = data.id || '';
                    document.getElementById('length').value = data.length || '';
                    document.getElementById('width').value = data.width || '';
                    document.getElementById('structureType').value = data.structure_type || '';
                    document.getElementById('spanCount').value = data.span_count || '';
                    document.getElementById('expansionJointLocations').value = data.expansion_joint_location || '';

                    // 브리지 데이터 업데이트
                    bridgeData = {
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

                    // 상태평가표 생성 버튼 활성화
                    const generateBtn = document.getElementById('generateEvaluation');
                    if (generateBtn) {
                        generateBtn.disabled = false;
                        console.log('상태평가표 생성 버튼 활성화됨');
                    }
                } else {
                    console.error('교량 데이터 로드 실패:', response.error);
                }
            },
            error: function(xhr, status, error) {
                console.error('교량 데이터 로드 실패:', error);
                alert('교량 데이터를 불러오는데 실패했습니다.');
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
            '방음판': 'railing',
            '차광망': 'railing',
            '낙석방지망': 'railing',
            '낙석방지책': 'railing',
            '중분대': 'railing',
            '중앙분리대': 'railing',
            '경계석': 'railing'
        };

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

    // 경간 생성 버튼 클릭 이벤트
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
        const fileId = bridgeSelect.val(); // 파일명을 file_id로 사용 (필요시 수정)

        // 입력값 검증
        if (!bridgeName || !structureType || isNaN(spanCount) || isNaN(length) || isNaN(width)) {
            alert('모든 필수 필드를 입력해주세요.');
            return;
        }

        if (spanCount < 1) {
            alert('경간 수는 1 이상이어야 합니다.');
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
                if (response.success) {
                    console.log('교량 정보 저장 성공');
                } else {
                    alert('교량 정보 저장 실패: ' + (response.error || '알 수 없는 오류'));
                }
            },
            error: function(xhr, status, error) {
                alert('교량 정보 저장 중 오류가 발생했습니다.');
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
            alert('교량 데이터 저장 중 오류가 발생했습니다.');
        }
    }

    // 교량 리스트 업데이트 함수
    function updateBridgeList() {
        const tbody = $('#bridgeListTable tbody');
        tbody.empty();

        if (savedBridges.length === 0) {
            tbody.append('<tr><td colspan="7" class="text-center">저장된 교량 데이터가 없습니다.</td></tr>');
        } else {
            savedBridges.forEach((bridge, index) => {
                const isSelected = bridgeData && bridgeData.name === bridge.name;
                const row = `
                    <tr class="bridge-row ${isSelected ? 'table-primary' : ''}" style="cursor: pointer; background-color: ${isSelected ? '' : '#ffffff'};">
                        <td>${bridge.name}</td>
                        <td>${bridge.structureType}</td>
                        <td>${bridge.length}</td>
                        <td>${bridge.width}</td>
                        <td>${bridge.spanCount}</td>
                        <td>${bridge.expansionJointLocations}</td>
                        <td>
                            <button class="btn btn-sm btn-primary edit-bridge" data-index="${index}">수정</button>
                            <button class="btn btn-sm btn-danger delete-bridge" data-index="${index}">삭제</button>
                        </td>
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
            if ($(e.target).hasClass('edit-bridge') || $(e.target).hasClass('delete-bridge')) {
                return;
            }

            // 이전 선택된 행의 하이라이트 제거
            $('.bridge-row').removeClass('table-primary').css('background-color', '#ffffff');

            // 현재 선택된 행 하이라이트
            $(this).addClass('table-primary').css('background-color', '');

            const index = $(this).find('.edit-bridge').data('index');
            const bridge = savedBridges[index];

            console.log('저장된 교량 선택:', bridge.name);

            // 현재 선택된 교량 데이터 설정
            bridgeData = bridge;

            // 모든 부재 체크박스 선택
            $('#slabCheck, #girderCheck, #crossbeamCheck, #abutmentCheck, #pierCheck, #bearingCheck, #expansionJointCheck, #pavementCheck, #drainageCheck, #railingCheck').prop('checked', true);

            // 부재 선택 카드 표시
            const componentCard = document.getElementById('componentSelectionCard');
            if (componentCard) {
                componentCard.style.display = 'block';
            }

            // 상태평가표 생성
            const selectedComponents = {
                slab: true,
                girder: true,
                crossbeam: true,
                abutment: true,
                pier: true,
                bearing: true,
                expansionJoint: true,
                pavement: true,
                drainage: true,
                railing: true
            };

            // 손상 데이터 생성
            generateDamageData();

            // 선택된 부재에 대해서만 상태평가표 생성
            Object.entries(selectedComponents).forEach(([component, isSelected]) => {
                if (isSelected) {
                    console.log(`${component} 상태평가표 생성 중...`);
                    generateEvaluationTable(component, damageData[component]);

                    // 개별 부재 카드 표시
                    const card = document.getElementById(`${component}EvaluationCard`);
                    if (card) {
                        card.style.display = 'block';
                        console.log(`${component}EvaluationCard 표시됨`);
                    }
                }
            });

            // 통합 상태평가표 생성
            generateTotalEvaluationTable(selectedComponents);

            // 결과 섹션 표시
            const resultsDiv = document.getElementById('evaluationResults');
            if (resultsDiv) {
                resultsDiv.style.display = 'block';
                console.log('상태평가표 결과 섹션 표시됨');
            }
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

    // 상태평가표 생성 버튼 클릭 이벤트
    $('#generateEvaluation').on('click', function() {
        console.log("상태평가표 생성 버튼 클릭됨");
        // 선택된 부재 확인
        const selectedComponents = {
            slab: $('#slabCheck').is(':checked'),
            girder: $('#girderCheck').is(':checked'),
            crossbeam: $('#crossbeamCheck').is(':checked'),
            abutment: $('#abutmentCheck').is(':checked'),
            pier: $('#pierCheck').is(':checked'),
            bearing: $('#bearingCheck').is(':checked'),
            expansionJoint: $('#expansionJointCheck').is(':checked'),
            pavement: $('#pavementCheck').is(':checked'),
            drainage: $('#drainageCheck').is(':checked'),
            railing: $('#railingCheck').is(':checked')
        };

        for (const [key, isChecked] of Object.entries(selectedComponents)) {
            if (isChecked) {
                $("a[href='#" + key + "EvaluationHeader']").css('display', 'block');
            } else {
                $("a[href='#" + key + "EvaluationHeader']").css('display', 'none');
            }
        }




        console.log('선택된 부재들:', selectedComponents);

        // 현재 선택된 파일명 가져오기
        const currentFilename = window.currentSelectedFilename;
        if (!currentFilename) {
            alert('교량을 먼저 선택해주세요.');
            return;
        }

        // 서버에서 상태평가 데이터 생성
        $.ajax({
            url: '/api/generate_evaluation_data',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                filename: currentFilename
            }),
            success: function(response) {
                console.log('상태평가 데이터 생성 성공:', response);

                if (response.success) {
                    // 서버에서 받은 데이터로 damageData 업데이트
                    damageData = response.data;

                    // 선택된 부재에 대해서만 상태평가표 생성
                    Object.entries(selectedComponents).forEach(([component, isSelected]) => {
                        if (isSelected) {
                            console.log(`${component} 상태평가표 생성 중...`);

                            // 실제 손상 데이터가 있으면 사용, 없으면 빈 데이터로 생성
                            const componentDamageData = damageData[component] || [];
                            generateEvaluationTable(component, componentDamageData);

                            // 개별 부재 카드 표시
                            const card = document.getElementById(`${component}EvaluationCard`);
                            if (card) {
                                card.style.display = 'block';
                                console.log(`${component}EvaluationCard 표시됨`);
                            }
                        } else {
                            const card = document.getElementById(`${component}EvaluationCard`);
                            if (card) {
                                card.style.display = 'none';
                            }
                        }
                    });

                    // 통합 상태평가표 생성
                    generateTotalEvaluationTable(selectedComponents);

                    // 결과 섹션 표시
                    const resultsDiv = document.getElementById('evaluationResults');
                    if (resultsDiv) {
                        resultsDiv.style.display = 'block';
                        console.log('상태평가표 결과 섹션 표시됨');
                    }

                    console.log("상태평가표 생성 완료");
                } else {
                    console.error('상태평가 데이터 생성 실패:', response.error);
                    alert('상태평가 데이터 생성에 실패했습니다: ' + response.error);
                }
            },
            error: function(xhr, status, error) {
                console.error('상태평가 데이터 생성 요청 실패:', error);
                alert('상태평가 데이터 생성 요청에 실패했습니다.');
            }
        });
    });

    // 출력 버튼 클릭 이벤트
    $('#printEvaluation').on('click', function() {
        window.print();
    });

    // 저장 버튼 클릭 이벤트
    $('#saveEvaluation').on('click', function() {
        saveEvaluationResults();
    });

    // 상태평가 결과 저장 함수
    function saveEvaluationResults() {
        const currentFilename = window.currentSelectedFilename;
        if (!currentFilename) {
            alert('교량을 먼저 선택해주세요.');
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
        const componentTypes = ['slab', 'girder', 'crossbeam', 'abutment', 'pier', 'bearing', 'expansionJoint', 'pavement', 'drainage', 'railing'];

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
                    alert('상태평가 결과가 저장되었습니다.');
                } else {
                    alert('저장에 실패했습니다: ' + response.error);
                }
            },
            error: function(xhr, status, error) {
                console.error('저장 요청 실패:', error);
                alert('저장 요청에 실패했습니다.');
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

        // 교량 경간에 따른 부재별 손상 데이터 생성
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
        $(document).on('change', '.area-input', function() {
            const $this = $(this);
            const newArea = parseFloat($this.val()) || 100;
            const $row = $this.closest('tr');
            const spanId = $row.find('td:first').text();

            console.log(`${spanId} 면적 변경: ${newArea}`);

            // 해당 행의 비율 재계산 및 등급 업데이트
            updateRowCalculations($row, newArea);
        });
    }

    // 행의 계산 업데이트
    function updateRowCalculations($row, newArea) {
        // 비율 계산 칸들을 찾아서 업데이트
        $row.find('[data-damage-quantity]').each(function() {
            const $cell = $(this);
            const damageQuantity = parseFloat($cell.data('damage-quantity')) || 0;
            const newRatio = newArea > 0 ? (damageQuantity / newArea) * 100 : 0;
            $cell.text(newRatio > 0 ? newRatio.toFixed(2) : '-');

            // 등급 업데이트
            const $gradeCell = $cell.next();
            if ($gradeCell.length) {
                $gradeCell.text(evaluateGrade(newRatio));
            }
        });

        // 최종 등급 재계산
        updateFinalGrade($row);
    }

    // 최종 등급 업데이트
    function updateFinalGrade($row) {
        const grades = [];
        $row.find('td').each(function() {
            const text = $(this).text().trim();
            if (['a', 'b', 'c', 'd', 'e'].includes(text)) {
                grades.push(text);
            }
        });

        // 가장 높은 등급 선택
        const gradeOrder = ['a', 'b', 'c', 'd', 'e'];
        let finalGrade = 'a';
        grades.forEach(grade => {
            if (gradeOrder.indexOf(grade) > gradeOrder.indexOf(finalGrade)) {
                finalGrade = grade;
            }
        });

        $row.find('td:last strong').text(finalGrade);
    }

    // 손상 데이터 생성에 필요한 보조 함수들
    function getRandomDamageValue(min, max) {
        return (Math.random() * (max - min) + min).toFixed(2);
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
});
