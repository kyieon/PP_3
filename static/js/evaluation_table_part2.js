                <td>${evalData.rebar_corrosion_ratio > 0 ? evalData.rebar_corrosion_ratio.toFixed(2) : '-'}</td><td>${evaluateGradeFromValue(evalData.rebar_corrosion_ratio)}</td>
                <td><strong>${evalData.grade || 'a'}</strong></td>
            </tr>
        `;
    }
    
    // 교대 테이블 행 생성 (서버 평가 데이터 기반)
    function generateAbutmentTableRowFromEvaluationData(spanId, evalData) {
        const area = evalData.inspection_area || 100;
        
        return `
            <tr>
                <td>${spanId}</td>
                <td><input type="number" class="form-control area-input" value="${area}" step="0.1"></td>
                <td>${evalData.crack_width > 0 ? evalData.crack_width.toFixed(2) : '-'}</td><td>${evaluateGradeFromValue(evalData.crack_width)}</td>
                <td>${evalData.deformation || '-'}</td><td>${evalData.deformation !== '-' ? 'b' : 'a'}</td>
                <td>${evalData.surface_damage_ratio > 0 ? evalData.surface_damage_ratio.toFixed(2) : '-'}</td><td>${evaluateGradeFromValue(evalData.surface_damage_ratio)}</td>
                <td>${evalData.rebar_corrosion_ratio > 0 ? evalData.rebar_corrosion_ratio.toFixed(2) : '-'}</td><td>${evaluateGradeFromValue(evalData.rebar_corrosion_ratio)}</td>
                <td><strong>${evalData.grade || 'a'}</strong></td>
            </tr>
        `;
    }
    
    // 교각 테이블 행 생성 (서버 평가 데이터 기반)
    function generatePierTableRowFromEvaluationData(spanId, evalData) {
        return `
            <tr>
                <td>${spanId}</td>
                <td>${evalData.crack_width > 0 ? evalData.crack_width.toFixed(2) : '-'}</td><td>${evaluateGradeFromValue(evalData.crack_width)}</td>
                <td>${evalData.damage_condition || '-'}</td><td>${evalData.damage_condition !== '-' ? 'b' : 'a'}</td>
                <td>${evalData.erosion || '-'}</td><td>${evalData.erosion !== '-' ? 'b' : 'a'}</td>
                <td>${evalData.settlement || '-'}</td><td>${evalData.settlement !== '-' ? 'b' : 'a'}</td>
                <td><strong>${evalData.grade || 'a'}</strong></td>
            </tr>
        `;
    }
    
    // 교량받침 테이블 행 생성 (서버 평가 데이터 기반)
    function generateBearingTableRowFromEvaluationData(spanId, evalData) {
        return `
            <tr>
                <td>${spanId}</td>
                <td>${evalData.body_condition || '-'}</td><td>${evalData.body_condition !== '-' ? 'c' : 'a'}</td>
                <td>${evalData.pad_condition || '-'}</td><td>${evalData.pad_condition !== '-' ? 'b' : 'a'}</td>
                <td><strong>${evalData.grade || 'a'}</strong></td>
            </tr>
        `;
    }
    
    // 신축이음 테이블 행 생성 (서버 평가 데이터 기반)
    function generateExpansionJointTableRowFromEvaluationData(spanId, evalData) {
        return `
            <tr>
                <td>${spanId}</td>
                <td colspan="2">${evalData.body_condition || '-'}</td>
                <td>${evalData.footer_crack || '-'}</td><td>${evalData.footer_crack !== '-' ? 'b' : 'a'}</td>
                <td>${evalData.section_damage || '-'}</td><td>${evalData.section_damage !== '-' ? 'b' : 'a'}</td>
                <td><strong>${evalData.grade || 'a'}</strong></td>
            </tr>
        `;
    }
    
    // 교면포장 테이블 행 생성 (서버 평가 데이터 기반)
    function generatePavementTableRowFromEvaluationData(spanId, evalData) {
        const area = evalData.inspection_area || 100;
        
        return `
            <tr>
                <td>${spanId}</td>
                <td><input type="number" class="form-control area-input" value="${area}" step="0.1"></td>
                <td>${evalData.damage_ratio > 0 ? evalData.damage_ratio.toFixed(2) : '-'}</td><td>${evaluateGradeFromValue(evalData.damage_ratio)}</td>
                <td>${evalData.traffic_condition || '양호'}</td><td>${evalData.traffic_condition !== '양호' ? 'b' : 'a'}</td>
                <td>${evalData.drainage_condition || '양호'}</td><td>${evalData.drainage_condition !== '양호' ? 'b' : 'a'}</td>
                <td><strong>${evalData.grade || 'a'}</strong></td>
            </tr>
        `;
    }
    
    // 배수시설 테이블 행 생성 (서버 평가 데이터 기반)
    function generateDrainageTableRowFromEvaluationData(spanId, evalData) {
        return `
            <tr>
                <td>${spanId}</td>
                <td>${evalData.outlet_condition || '-'}</td><td>${evalData.outlet_condition !== '-' ? 'b' : 'a'}</td>
                <td>${evalData.pipe_condition || '-'}</td><td>${evalData.pipe_condition !== '-' ? 'b' : 'a'}</td>
                <td><strong>${evalData.grade || 'a'}</strong></td>
            </tr>
        `;
    }
    
    // 난간 및 연석 테이블 행 생성 (서버 평가 데이터 기반)
    function generateRailingTableRowFromEvaluationData(spanId, evalData) {
        const length = evalData.length || 100;
        
        return `
            <tr>
                <td>${spanId}</td>
                <td><input type="number" class="form-control area-input" value="${length}" step="0.1"></td>
                <td>${evalData.surface_damage_ratio > 0 ? evalData.surface_damage_ratio.toFixed(2) : '-'}</td><td>${evaluateGradeFromValue(evalData.surface_damage_ratio)}</td>
                <td>${evalData.rebar_corrosion_ratio > 0 ? evalData.rebar_corrosion_ratio.toFixed(2) : '-'}</td><td>${evaluateGradeFromValue(evalData.rebar_corrosion_ratio)}</td>
                <td><strong>${evalData.grade || 'a'}</strong></td>
            </tr>
        `;
    }
    
    // 값으로부터 등급 평가하는 함수
    function evaluateGradeFromValue(value) {
        if (value === '-' || value === null || value === undefined || value === 0) {
            return 'a';
        }
        
        const numValue = parseFloat(value);
        
        if (numValue >= 1.0) {
            return 'e';
        } else if (numValue >= 0.5) {
            return 'd';
        } else if (numValue >= 0.3) {
            return 'c';
        } else if (numValue >= 0.1) {
            return 'b';
        } else {
            return 'a';
        }
    }
    
    // 빈 테이블 행 생성
    function generateEmptyTableRow(componentType, spanId, inspectionArea) {
        let emptyRow = `<tr><td>${spanId}</td>`;
        
        switch(componentType) {
            case 'slab':
                emptyRow += `<td><input type="number" class="form-control area-input" value="${inspectionArea}" step="0.1"></td>`;
                emptyRow += '<td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                break;
            case 'girder':
                emptyRow += `<td><input type="number" class="form-control area-input" value="${inspectionArea}" step="0.1"></td>`;
                emptyRow += '<td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                break;
            case 'crossbeam':
                emptyRow += `<td><input type="number" class="form-control area-input" value="${inspectionArea}" step="0.1"></td>`;
                emptyRow += '<td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                break;
            case 'abutment':
                emptyRow += `<td><input type="number" class="form-control area-input" value="${inspectionArea}" step="0.1"></td>`;
                emptyRow += '<td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                break;
            case 'pier':
                emptyRow += '<td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                break;
            case 'bearing':
                emptyRow += '<td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                break;
            case 'expansionJoint':
                emptyRow += '<td colspan="2">-</td><td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                break;
            case 'pavement':
                emptyRow += `<td><input type="number" class="form-control area-input" value="${inspectionArea}" step="0.1"></td>`;
                emptyRow += '<td>-</td><td>a</td><td>양호</td><td>a</td><td>양호</td><td>a</td><td><strong>a</strong></td>';
                break;
            case 'drainage':
                emptyRow += '<td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                break;
            case 'railing':
                emptyRow += `<td><input type="number" class="form-control area-input" value="${inspectionArea}" step="0.1"></td>`;
                emptyRow += '<td>-</td><td>a</td><td>-</td><td>a</td><td><strong>a</strong></td>';
                break;
        }
        emptyRow += '</tr>';
        return emptyRow;
    }

    // 부재별 테이블 헤더 생성 함수들
    function generateSlabTableHeader() {
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

    function generateGirderTableHeader() {
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

    function generateCrossbeamTableHeader() {
        return `
            <thead>
                <tr>
                    <th rowspan="2">구분</th>
                    <th rowspan="2">점검<br>면적<br>(m²)</th>
                    <th colspan="2">균열</th>
                    <th colspan="2">표면손상</th>
                    <th colspan="2">철근부식</th>
                    <th rowspan="2">상태평가 결과</th>
                </tr>
                <tr>
                    <th>최대폭</th>
                    <th>등급</th>
                    <th>면적율</th>
                    <th>등급</th>
                    <th>면적율</th>
                    <th>등급</th>
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

    function generatePierTableHeader() {
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

    function generateBearingTableHeader() {
        return `
            <thead>
                <tr>
                    <th rowspan="2">구 분</th>
                    <th colspan="2">베어링 본체</th>
                    <th colspan="2">교량받침 패드</th>
                    <th rowspan="2">상태평가<br>결과</th>
                </tr>
                <tr>
                    <th>손상현황</th>
                    <th>평가</th>
                    <th>손상현황</th>
                    <th>평가</th>
                </tr>
            </thead>
        `;
    }

    function generateExpansionJointTableHeader() {
        return `
            <thead>
                <tr>
                    <th rowspan="2">구 분</th>
                    <th rowspan="2" colspan="2">본체</th>
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
                        <th colspan="5">포장불량</th>
                        <th rowspan="2">배수</th>
                        <th rowspan="2">상태평가<br>결과</th>
                    </tr>
                    <tr>
                        <th>포장불량<br>면적율(%)</th>
                        <th>평가</th>
                        <th>포장손상에<br>따른 주행성</th>
                        <th>평가</th>
                        <th>배수구 막힘</th>
                    </tr>
                </thead>
        `;
    }

    function generateDrainageTableHeader() {
        return `
            <thead>
                <tr>
                    <th rowspan="2">구분</th>
                    <th colspan="2">배수구</th>
                    <th colspan="2">배수관</th>
                    <th rowspan="2">상태평가 결과</th>
                </tr>
                <tr>
                    <th>손상상태</th>
                    <th>평가</th>
                    <th>손상상태</th>
                    <th>평가</th>
                </tr>
            </thead>
        `;
    }

    function generateRailingTableHeader() {
        return `
            <thead>
                <tr>
                    <th rowspan="2">구 분</th>
                    <th rowspan="2">길이<br>(m)</th>
                    <th colspan="4">열화 및 손상</th>
                    <th rowspan="2">상태<br>평가<br>결과</th>
                </tr>
                <tr>
                    <th colspan="2">표면손상<br>면적율(%)</th>
                    <th colspan="2">철근부식<br>손상면적율(%)</th>
                </tr>
            </thead>
        `;
    }
    
    /**
     * 통합 상태평가표 생성
     */
    function generateTotalEvaluationTable(selectedComponents) {
        const tableElement = document.getElementById('totalEvaluationTable');
        
        let tableHtml = `
            <thead>
                <tr>
                    <th rowspan="2">부재의 분류</th>
                    <th rowspan="2">구조형식</th>
                    <th colspan="2">상부구조</th>
                    <th>2차부재</th>
                    <th colspan="4">기타부재</th>
                    <th>받침</th>
                    <th colspan="2">하부구조</th>
                    <th colspan="2">내구성 요소</th>
                    <th rowspan="2">상태평가 결과</th>
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
                    <th>탄산화_상부</th>
                    <th>탄산화_하부</th>
                </tr>
            </thead>
            <tbody>
        `;
        
        // 구조형식 선택값 가져오기
        const structureType = document.getElementById('structureType').value;
        const weights = STRUCTURE_WEIGHTS[structureType] || {};
        
        // 선택된 부재에 대해서만 데이터 추가
        const rowData = {
            '구조형식': structureType,
            '바닥판': selectedComponents.slab ? getComponentGrade('slab') : '-',
            '거더': selectedComponents.girder ? getComponentGrade('girder') : '-',
            '가로보': selectedComponents.crossbeam ? getComponentGrade('crossbeam') : '-',
            '포장': selectedComponents.pavement ? getComponentGrade('pavement') : '-',
            '배수': selectedComponents.drainage ? getComponentGrade('drainage') : '-',
            '난간연석': selectedComponents.railing ? getComponentGrade('railing') : '-',
            '신축이음': selectedComponents.expansionJoint ? getComponentGrade('expansionJoint') : '-',
            '교량받침': selectedComponents.bearing ? getComponentGrade('bearing') : '-',
            '하부': selectedComponents.pier ? getComponentGrade('pier') : '-',
            '기초': selectedComponents.abutment ? getComponentGrade('abutment') : '-',
            '탄산화_상부': '-',
            '탄산화_하부': '-'
        };
        
        // 데이터 행 추가
            tableHtml += `
                <tr>
                <td>${rowData['구조형식']}</td>
                <td>${rowData['구조형식']}</td>
                <td>${rowData['바닥판']}</td>
                <td>${rowData['거더']}</td>
                <td>${rowData['가로보']}</td>
                <td>${rowData['포장']}</td>
                <td>${rowData['배수']}</td>
                <td>${rowData['난간연석']}</td>
                <td>${rowData['신축이음']}</td>
                <td>${rowData['교량받침']}</td>
                <td>${rowData['하부']}</td>
                <td>${rowData['기초']}</td>
                <td>${rowData['탄산화_상부']}</td>
                <td>${rowData['탄산화_하부']}</td>
                <td>${calculateOverallRating(Object.values(rowData))}</td>
                </tr>
            `;
        
        // 가중치 행 생성
        tableHtml += `
            <tr>
                <td colspan="2">가중치</td>
                <td>${weights['바닥판'] ?? '-'}</td>
                <td>${weights['거더'] ?? '-'}</td>
                <td>${weights['2차부재'] ?? '-'}</td>
                <td>${weights['교량받침'] ?? '-'}</td>
                <td>${weights['난간/연석'] ?? '-'}</td>
                <td>${weights['신축이음'] ?? '-'}</td>
                <td>${weights['교대/교각'] ?? '-'}</td>
                <td>${weights['기초'] ?? '-'}</td>
                <td>${weights['교면포장'] ?? '-'}</td>
                <td>${weights['배수시설'] ?? '-'}</td>
                <td>${weights['탄산화_상부'] ?? '-'}</td>
                <td>${weights['탄산화_하부'] ?? '-'}</td>
                <td>-</td>
            </tr>
        `;
        
        // 결함도 점수 및 가중평균 계산 함수도 동일하게 weights를 사용하도록 수정
        function calculateWeightedSum(averages, weights) {
            let weightedSum = 0;
            Object.keys(averages).forEach(component => {
                if (weights[component]) {
                    weightedSum += averages[component] * weights[component];
                }
            });
            return weightedSum;
        }

        function calculateTotalWeight(weights) {
            let totalWeight = 0;
            Object.values(weights).forEach(w => {
                if (typeof w === 'number') totalWeight += w;
            });
            return totalWeight;
        }

        // 결함도 점수 계산도 동일하게 적용
        function calculateDefectScore(rowData, weights) {
            let totalScore = 0;
            let totalWeight = 0;
            Object.entries(rowData).forEach(([component, grade]) => {
                if (weights[component] && grade_to_defect_score) {
                    totalScore += grade_to_defect_score(grade) * weights[component];
                    totalWeight += weights[component];
                }
            });
            if (totalWeight === 0) return null;
            return totalScore / totalWeight;
        }
        
        // 환산 결함도 점수 점수 행
        tableHtml += `
            <tr>
                <td colspan="14">환산 결함도 점수</td>
                <td>${calculateDefectScore(rowData, weights).toFixed(3)}</td>
            </tr>
        `;
        
        // 최종 상태평가 결과 행
        tableHtml += `
            <tr>
                <td colspan="14">상태평가 결과</td>
                <td>${getConditionGrade(calculateDefectScore(rowData, weights))}</td>
            </tr>
        `;
        
        tableHtml += '</tbody>';
        tableElement.innerHTML = tableHtml;
    }
    
    // 부재별 등급 가져오기 함수
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
    
    // 상태등급 계산
    function getConditionGrade(defectScore) {
        if (defectScore <= 1.5) return 'A';
        if (defectScore <= 2.5) return 'B';
        if (defectScore <= 3.5) return 'C';
        if (defectScore <= 4.5) return 'D';
        return 'E';
    }
    
    /**
     * 등급 평가 함수
     * @param {*} value - 평가할 값
     * @returns {string} 등급 (a~e)
     */
    function evaluateGrade(value) {
        if (value === '-' || value === null || value === undefined) {
            return 'a';
        }
        
        value = parseFloat(value);
        
        if (value >= 1.0) {
            return 'e';
        } else if (value >= 0.5) {
            return 'd';
        } else if (value >= 0.3) {
            return 'c';
        } else if (value >= 0.1) {
            return 'b';
        } else {
            return 'a';
        }
    }
    
    /**
     * 바닥판 상태평가 함수
     */
    function evaluateSlabCondition(crackWidth, crackRatio, leakRatio, surfaceDamageRatio, rebarCorrosionRatio) {
        let grade = 'a';
        let hasAnyDamage = false;
        
        // 균열폭 기준
        if (crackWidth !== '-' && crackWidth !== null && crackWidth !== undefined) {
            hasAnyDamage = true;
            const width = parseFloat(crackWidth);
            
            if (width >= 1.0) {
                return 'e';
            } else if (width >= 0.5) {
                grade = grade < 'd' ? 'd' : grade;
            } else if (width >= 0.3) {
                grade = grade < 'c' ? 'c' : grade;
            } else if (width >= 0.1) {
                grade = grade < 'b' ? 'b' : grade;
            }
        }
        
        // 균열률 기준
        if (crackRatio !== '-' && crackRatio !== null && crackRatio !== undefined) {
            hasAnyDamage = true;
            const ratio = parseFloat(crackRatio);
            
            if (ratio >= 20) {
                return 'e';
            } else if (ratio >= 10) {
                grade = grade < 'd' ? 'd' : grade;
            } else if (ratio >= 2) {
                grade = grade < 'c' ? 'c' : grade;
            } else if (ratio > 0) {
                grade = grade < 'b' ? 'b' : grade;
            }
        }
        
        // 누수 및 백태 기준
        if (leakRatio !== '-' && leakRatio !== null && leakRatio !== undefined) {
            hasAnyDamage = true;
            const ratio = parseFloat(leakRatio);
            
            if (ratio >= 10) {
                grade = grade < 'c' ? 'c' : grade;
            } else if (ratio > 0) {
                grade = grade < 'b' ? 'b' : grade;
            }
        }
        
        // 표면손상 기준
        if (surfaceDamageRatio !== '-' && surfaceDamageRatio !== null && surfaceDamageRatio !== undefined) {
            hasAnyDamage = true;
            const ratio = parseFloat(surfaceDamageRatio);
            
            if (ratio >= 10) {
                grade = grade < 'd' ? 'd' : grade;
            } else if (ratio >= 2) {
                grade = grade < 'c' ? 'c' : grade;
            } else if (ratio > 0) {
                grade = grade < 'b' ? 'b' : grade;
            }
        }
        
        // 철근부식 기준
        if (rebarCorrosionRatio !== '-' && rebarCorrosionRatio !== null && rebarCorrosionRatio !== undefined) {
            hasAnyDamage = true;
            const ratio = parseFloat(rebarCorrosionRatio);
            
            if (ratio >= 2) {
                grade = grade < 'd' ? 'd' : grade;
            } else if (ratio > 0) {
                grade = grade < 'c' ? 'c' : grade;
            }
        }
        
        // 손상이 전혀 없는 경우
        if (!hasAnyDamage) {
            grade = 'a';
        }
        
        return grade;
    }
    
});
