// 신축이음 상태평가표 생성 함수 수정

// 기존 generateEvaluationTable 함수에서 신축이음 부분만 수정
function generateEvaluationTable(componentType, data) {
    const tableElement = document.getElementById(`${componentType}EvaluationTable`);
    if (!tableElement) return;

    console.log(`${componentType} 상태평가표 생성 시작, 데이터:`, data);

    let tableHtml = '';
    // 부재별 테이블 헤더 생성
    switch(componentType) {
        case 'slab':
            tableHtml = generateSlabTableHeader();
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
    
    // 사용자 입력 면적 기본값 100
    const defaultInspectionArea = 100;
    
    // 신축이음의 경우 별도 처리
    if (componentType === 'expansionJoint') {
        console.log('신축이음 별도 처리 시작, 신축이음 위치:', bridgeData.expansionJointLocations);
        console.log('전체 데이터:', data);
        
        // 신축이음 위치 데이터를 직접 사용
        const expansionLocations = bridgeData.expansionJointLocations ? 
            bridgeData.expansionJointLocations.split(',').map(loc => loc.trim()).filter(loc => loc) : [];
        
        console.log('파싱된 신축이음 위치 배열:', expansionLocations);
        
        if (expansionLocations.length > 0) {
            // 설정된 신축이음 위치에 따라 행 생성
            expansionLocations.forEach(location => {
                console.log(`신축이음 위치 ${location}에 대한 행 생성`);
                
                // 해당 위치의 실제 데이터 검색
                const spanDamageData = data.filter ? data.filter(d => d.span_id === location) : [];
                
                if (spanDamageData.length > 0) {
                    console.log(`실제 데이터 있음: ${location}`, spanDamageData[0]);
                    tableHtml += generateTableRowFromData(componentType, location, spanDamageData[0], defaultInspectionArea);
                } else {
                    console.log(`실제 데이터 없음, 빈 행 생성: ${location}`);
                    tableHtml += generateEmptyTableRow(componentType, location, defaultInspectionArea);
                }
            });
        } else {
            // 신축이음 위치 정보가 없으면 기본값으로 A1, A2 생성
            console.log('신축이음 위치 정보 없음, 기본 A1, A2 행 생성');
            const defaultExpansionLocations = ['A1', 'A2'];
            
            defaultExpansionLocations.forEach(location => {
                console.log(`기본 신축이음 위치 ${location}에 대한 행 생성`);
                
                // 해당 위치의 실제 데이터 검색
                const spanDamageData = data.filter ? data.filter(d => d.span_id === location) : [];
                
                if (spanDamageData.length > 0) {
                    console.log(`실제 데이터 있음: ${location}`, spanDamageData[0]);
                    tableHtml += generateTableRowFromData(componentType, location, spanDamageData[0], defaultInspectionArea);
                } else {
                    console.log(`실제 데이터 없음, 빈 행 생성: ${location}`);
                    tableHtml += generateEmptyTableRow(componentType, location, defaultInspectionArea);
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
                // 기초는 A1, P1, P2, ..., A2 순서로 출력
                valid = span.id.startsWith('A') || span.id.startsWith('P');
            }
            
            if (!valid) return;
            
            // 해당 경간의 손상 데이터 수집
            const spanDamageData = data.filter ? data.filter(d => d.span_id === span.id) : [];
            
            if (spanDamageData.length > 0) {
                // 실제 데이터를 기반으로 테이블 행 생성
                tableHtml += generateTableRowFromData(componentType, span.id, spanDamageData[0], defaultInspectionArea);
            } else {
                // 데이터가 없으면 기본값으로 표시
                tableHtml += generateEmptyTableRow(componentType, span.id, defaultInspectionArea);
            }
        });
    } else {
        // spans 데이터가 없으면 기본 경간 생성
        const defaultSpans = componentType === 'expansionJoint' ? ['A1', 'A2'] : ['S1', 'S2', 'S3'];
        defaultSpans.forEach(spanId => {
            const spanDamageData = data.filter ? data.filter(d => d.span_id === spanId) : [];
            if (spanDamageData.length > 0) {
                tableHtml += generateTableRowFromData(componentType, spanId, spanDamageData[0], defaultInspectionArea);
            } else {
                tableHtml += generateEmptyTableRow(componentType, spanId, defaultInspectionArea);
            }
        });
    }
    
    tableHtml += '</tbody>';
    tableElement.innerHTML = tableHtml;
    
    console.log(`${componentType} 상태평가표 생성 완료`);
}

console.log('신축이음 수정 스크립트가 로드되었습니다.');
