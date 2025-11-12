// 구조형식별 가중치 사전 정의
const STRUCTURE_WEIGHTS = {
    'PSC BOX': {
        '바닥판': 20,
        '교량받침': 9,
        '난간/연석': 2,
        '2차부재': 3,
        '거더': 20,
        '교대/교각': 13,
        '기초': 7,
        '신축이음': 9,
        '교면포장': 7,
        '배수시설': 3,
        '탄산화_상부': 4,
        '탄산화_하부': 3,
    },
    'PSCI': {
        '바닥판': 18,
        '교량받침': 9,
        '난간/연석': 2,
        '거더': 20,
        '2차부재': 5,
        '교대/교각': 13,
        '기초': 7,
        '신축이음': 9,
        '교면포장': 7,
        '배수시설': 3,
        '탄산화_상부': 4,
        '탄산화_하부': 3,
    },
    'STB': {
        '바닥판': 18,
        '교량받침': 9,
        '난간/연석': 2,
        '거더': 20,
        '2차부재': 5,
        '교대/교각': 13,
        '기초': 7,
        '신축이음': 9,
        '교면포장': 7,
        '배수시설': 3,
        '탄산화_상부': 4,
        '탄산화_하부': 3,
    },
    'RCS': {
        '슬래브': 34,
        '신축이음': 10,
        '난간/연석': 2,
        '교량받침': 10,
        '교대/교각': 20,
        '교면포장': 7,
        '탄산화_상부': 4,
        '기초': 7,
        '배수시설': 3,
        '탄산화_하부': 3,
    },
    '일반거더교': {
        '바닥판': 18,
        '교량받침': 9,
        '난간/연석': 2,
        '거더': 20,
        '2차부재': 5,
        '교대/교각': 13,
        '기초': 7,
        '신축이음': 9,
        '교면포장': 7,
        '배수시설': 3,
        '탄산화_상부': 4,
        '탄산화_하부': 3,
    },
    'RA(거더없음)': {
        '바닥판': 34,
        '교량받침': 3,
        '신축이음': 3,
        '교대/교각': 34,
        '교면포장': 7,
        '기초': 7,
        '배수시설': 3,
        '난간/연석': 2,
        '탄산화_상부': 4,
        '탄산화_하부': 3,
    },
    'RA(거더있음)': {
        '바닥판': 20,
        '거더': 21,
        '2차부재': 5,
        '교량받침': 3,
        '신축이음': 3,
        '교대/교각': 22,
        '교면포장': 7,
        '기초': 7,
        '배수시설': 3,
        '난간/연석': 2,
        '탄산화_상부': 4,
        '탄산화_하부': 3,
    },
    '강바닥판거더교': {
        '바닥판': 20,
        '교량받침': 9,
        '난간/연석': 2,
        '거더': 18,
        '2차부재': 5,
        '교대/교각': 13,
        '기초': 7,
        '신축이음': 9,
        '교면포장': 7,
        '배수시설': 3,
        '탄산화_상부': 4,
        '탄산화_하부': 3,
    }
};

// 값으로부터 등급 평가하는 함수
function evaluateGrade(value, damageType = 'crack_width') {
    if (value === '-' || value === null || value === undefined || value === 0) {
        return 'a';
    }

    const numValue = parseFloat(value);

    // NaN 처리 추가
    if (isNaN(numValue)) {
        return 'a';
    }

    // 손상 유형별 평가 기준 적용
    switch (damageType) {
        case 'crack_width':
            // 균열폭 기준 (일반 바닥판)
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

        case 'crack_width_psc':
            // 균열폭 기준 (프리스트레스 바닥판)
            if (numValue >= 0.5) {
                return 'e';
            } else if (numValue >= 0.3) {
                return 'd';
            } else if (numValue >= 0.2) {
                return 'c';
            } else {
                return 'b';
            }

        case 'crack_ratio':
            // 균열률 기준
            if (numValue >= 20) {
                return 'e';
            } else if (numValue >= 10) {
                return 'd';
            } else if (numValue >= 2) {
                return 'c';
            } else if (numValue > 0) {
                return 'b';
            } else {
                return 'a';
            }

        case 'leak_ratio':
            // 누수 및 백태 기준
            if (numValue >= 10) {
                return 'c';
            } else if (numValue > 0) {
                return 'b';
            } else {
                return 'a';
            }

        case 'surface_damage_ratio':
            // 표면손상 기준
            if (numValue >= 10) {
                return 'd';
            } else if (numValue >= 2) {
                return 'c';
            } else if (numValue > 0) {
                return 'b';
            } else {
                return 'a';
            }

        case 'rebar_corrosion_ratio':
            // 철근 부식 기준
            if (numValue >= 2) {
                return 'd';
            } else if (numValue > 0) {
                return 'c';
            } else {
                return 'a';
            }

        case 'main_rust_area':
            // 주부재 부식 (강재)
            if (numValue >= 10) {
                return 'e';
            } else if (numValue >= 2) {
                return 'd';
            } else if (numValue > 0) {
                return 'c';
            } else {
                return 'a';
            }

        case 'sub_rust_area':
            // 보조부재 부식 (강재)
            if (numValue >= 10) {
                return 'd';
            } else if (numValue >= 2) {
                return 'c';
            } else if (numValue > 0) {
                return 'b';
            } else {
                return 'a';
            }

        case 'section_loss_area':
            // 단면손실 (강재)
            if (numValue >= 10) {
                return 'e';
            } else if (numValue >= 2) {
                return 'd';
            } else {
                return 'a';
            }

        case 'wire_break_ratio':
            // 소선 단선율 (케이블)
            if (numValue >= 10) {
                return 'e';
            } else if (numValue >= 2) {
                return 'd';
            } else if (numValue > 0) {
                return 'c';
            } else {
                return 'a';
            }

        case 'corrosion_length_ratio':
            // 점녹/부식 길이 비율 (케이블)
            if (numValue >= 2) {
                return 'd';
            } else if (numValue > 0.1) {
                return 'c';
            } else if (numValue > 0) {
                return 'b';
            } else {
                return 'a';
            }

        case 'sheath_damage_ratio':
            // 보호관 손상 길이 비율 (케이블)
            if (numValue >= 10) {
                return 'd';
            } else if (numValue >= 2) {
                return 'c';
            } else if (numValue > 0) {
                return 'b';
            } else {
                return 'a';
            }

        case 'paint_damage_ratio':
            // 도장 불량 비율 (난간/연석)
            if (numValue >= 10) {
                return 'c';
            } else if (numValue > 0) {
                return 'b';
            } else {
                return 'a';
            }

        case 'section_loss_ratio':
        case 'spalling_or_exposed_rebar_ratio':
            // 단면 손상/파손 비율, 박리/철근노출 비율 (난간/연석)
            if (numValue >= 10) {
                return 'd';
            } else if (numValue > 0) {
                return 'c';
            } else {
                return 'a';
            }

        case 'rebar_corrosion_length_ratio':
            // 철근 부식 길이 비율 (난간/연석)
            if (numValue >= 2) {
                return 'd';
            } else if (numValue > 0) {
                return 'c';
            } else {
                return 'a';
            }

        case 'damage_ratio_asphalt':
            // 포장불량률 (아스팔트)
            if (numValue >= 10) {
                return 'd';
            } else if (numValue >= 5) {
                return 'c';
            } else if (numValue > 0) {
                return 'b';
            } else {
                return 'a';
            }

        case 'damage_ratio_concrete':
        // 포장불량률 (콘크리트)
        if (numValue >= 30) {
        return 'd';
        } else if (numValue >= 10) {
        return 'c';
        } else if (numValue > 0) {
        return 'b';
        } else {
        return 'a';
        }


        default:
            // 기본 균열폭 기준
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
}

// 기초 상태평가 함수
function evaluateFoundationCondition(crack_width = null, section_loss = false,
                                    rebar_exposed = false, settlement_or_scour = false,
                                    severe_risk = false, other_damage = false) {
    /**
     * 기초 상태평가 등급(a~e)을 반환하는 함수
     *
     * @param {number|null} crack_width - 직접기초 상부 균열폭 (mm)
     * @param {boolean} section_loss - 단면손상 발생 여부
     * @param {boolean} rebar_exposed - 철근 노출 여부
     * @param {boolean} settlement_or_scour - 부등침하, 측방유동, 전반적 노출 등
     * @param {boolean} severe_risk - 단차, 상부구조 파손 등 구조적 위험 여부 (True → e)
     * @param {boolean} other_damage - 기타 손상 (기준 외 항목 포함)
     * @returns {string} 상태평가 등급: 'a', 'b', 'c', 'd', 'e'
     */

    console.log('기초 상태평가 시작:', {
        crack_width, section_loss, rebar_exposed,
        settlement_or_scour, severe_risk, other_damage
    });

    let grade = 'a';
    let has_any_damage = false;

    // 심각한 위험이 있으면 무조건 e등급
    if (severe_risk) {
        console.log('심각한 위험 감지 - e등급 적용');
        return 'e';
    }

    // 균열폭 평가
    if (crack_width !== null && crack_width !== undefined && crack_width > 0) {
        has_any_damage = true;
        const numCrackWidth = parseFloat(crack_width);
        if (!isNaN(numCrackWidth)) {
            if (numCrackWidth >= 0.3) {
                grade = maxGrade(grade, 'c');
                console.log('균열폭', numCrackWidth, 'mm - c등급 적용');
            } else {
                grade = maxGrade(grade, 'b');
                console.log('균열폭', numCrackWidth, 'mm - b등급 적용');
            }
        }
    }

    // 단면손상 평가
    if (section_loss) {
        has_any_damage = true;
        grade = maxGrade(grade, 'c');
        console.log('단면손상 감지 - c등급 적용');
    }

    // 철근노출 평가
    if (rebar_exposed) {
        has_any_damage = true;
        grade = maxGrade(grade, 'd');
        console.log('철근노출 감지 - d등급 적용');
    }

    // 부등침하, 측방유동, 전반적 노출 등
    if (settlement_or_scour) {
        has_any_damage = true;
        grade = maxGrade(grade, 'd');
        console.log('침하/세굴 감지 - d등급 적용');
    }

    // 기타 손상
    if (other_damage) {
        has_any_damage = true;
        grade = maxGrade(grade, 'c');
        console.log('기타 손상 감지 - c등급 적용');
    }

    // 손상이 전혀 없으면 b등급
    if (!has_any_damage) {
        grade = 'b';
        console.log('손상 없음 - b등급 적용');
    }

    console.log('기초 상태평가 결과:', grade);
    return grade;
}

// 최고 등급을 반환하는 헬퍼 함수
function maxGrade(grade1, grade2) {
    /**
     * 두 등급 중 더 높은 등급을 반환하는 함수
     *
     * @param {string} grade1 - 등급 1
     * @param {string} grade2 - 등급 2
     * @returns {string} 더 높은 등급
     */
    const grades = ['a', 'b', 'c', 'd', 'e'];
    const index1 = grades.indexOf(grade1.toLowerCase());
    const index2 = grades.indexOf(grade2.toLowerCase());

    if (index1 === -1) return grade2;
    if (index2 === -1) return grade1;

    return grades[Math.max(index1, index2)];
}

// 교량받침 상태평가 함수
function evaluateBearingCondition(rubber_split = false, rubber_bulging = false,
                                  shear_deformation = '정상', corrosion_area = '없음',
                                  crack_width = null, structural_failure = false,
                                  other_damage = false) {
    /**
     * 교량받침 상태평가 등급(a~e)을 반환하는 함수
     *
     * @param {boolean} rubber_split - 고무재 갈라짐 여부
     * @param {boolean} rubber_bulging - 고무재 부풀음 여부
     * @param {string} shear_deformation - 전단변형 상태 ('정상', '0.7T 이상', '1.5T 이상')
     * @param {string} corrosion_area - 부식/부착불량 면적 수준 ('없음', '일부', '1/2 이상')
     * @param {number|null} crack_width - 받침 관련 균열폭 (mm)
     * @param {boolean} structural_failure - 구조기능 상실 우려 여부
     * @param {boolean} other_damage - 기타 손상 여부
     * @returns {string} 상태평가 등급: 'a', 'b', 'c', 'd', 'e'
     */

    console.log('교량받침 상태평가 시작:', {
        rubber_split, rubber_bulging, shear_deformation, corrosion_area,
        crack_width, structural_failure, other_damage
    });

    let grade = 'a';
    let has_any_damage = false;

    // 1. 구조적 위험
    if (structural_failure) {
        console.log('구조기능 상실 - e등급 적용');
        return 'e';
    }

    // 2. 부식/부착불량
    if (corrosion_area === '1/2 이상') {
        console.log('부식/부착불량 1/2 이상 - e등급 적용');
        return 'e';
    } else if (corrosion_area === '일부') {
        has_any_damage = true;
        grade = maxGrade(grade, 'd');
        console.log('부식/부착불량 일부 - d등급 적용');
    }

    // 3. 전단변형량
    if (shear_deformation === '1.5T 이상') {
        has_any_damage = true;
        grade = maxGrade(grade, 'd');
        console.log('전단변형 1.5T 이상 - d등급 적용');
    } else if (shear_deformation === '0.7T 이상') {
        has_any_damage = true;
        grade = maxGrade(grade, 'c');
        console.log('전단변형 0.7T 이상 - c등급 적용');
    }

    // 4. 고무재 손상
    if (rubber_split) {
        has_any_damage = true;
        if (rubber_bulging) {
            grade = maxGrade(grade, 'd');
            console.log('고무재 갈라짐+부풀음 - d등급 적용');
        } else {
            grade = maxGrade(grade, 'c');
            console.log('고무재 갈라짐 - c등급 적용');
        }
    }

    // 5. 균열 평가 (모든 종류 포함)
    if (crack_width !== null && crack_width !== undefined && crack_width > 0) {
        has_any_damage = true;
        const numCrackWidth = parseFloat(crack_width);
        if (!isNaN(numCrackWidth)) {
            if (numCrackWidth >= 1.0) {
                console.log('균열폭', numCrackWidth, 'mm - e등급 적용');
                return 'e';
            } else if (numCrackWidth >= 0.5) {
                grade = maxGrade(grade, 'd');
                console.log('균열폭', numCrackWidth, 'mm - d등급 적용');
            } else if (numCrackWidth >= 0.3) {
                grade = maxGrade(grade, 'c');
                console.log('균열폭', numCrackWidth, 'mm - c등급 적용');
            } else if (numCrackWidth >= 0.1) {
                grade = maxGrade(grade, 'b');
                console.log('균열폭', numCrackWidth, 'mm - b등급 적용');
            }
        }
    }

    // 6. 기타 손상
    if (other_damage) {
        has_any_damage = true;
        grade = maxGrade(grade, 'b');
        console.log('기타 손상 감지 - b등급 적용');
    }

    // 7. 손상 없음
    if (!has_any_damage) {
        grade = 'a';
        console.log('손상 없음 - a등급 적용');
    }

    console.log('교량받침 상태평가 결과:', grade);
    return grade;
}

// 신축이음 상태평가 함수
function evaluateExpansionJoint(aging_or_dirt = false, function_degradation = false,
                               impact_or_noise = false, structural_damage = false,
                               other_damage = false) {
    /**
     * 신축이음 상태평가 등급(a~d)을 반환하는 함수
     *
     * @param {boolean} aging_or_dirt - 토사, 이물질, 퇴적, 균열
     * @param {boolean} function_degradation - 불량, 물받이, 볼트, 너트, 탈락, 유간, 부식, 파손, 박리, 박락
     * @param {boolean} impact_or_noise - 강판, 이상음, 밀착, 거동, 지장, 충격, 심한 파손, 심한 단차
     * @param {boolean} structural_damage - 본체 파손, 본체 탈락, 작동 불능
     * @param {boolean} other_damage - 기타 손상 (기준 외 항목 포함)
     * @returns {string} 상태평가 등급: 'a', 'b', 'c', 'd'
     */

    console.log('신축이음 상태평가 시작:', {
        aging_or_dirt, function_degradation, impact_or_noise, structural_damage, other_damage
    });

    let grade = 'a';

    if (structural_damage) {
        console.log('구조적 손상 감지 - d등급 적용');
        return 'd';
    }

    if (impact_or_noise) {
        grade = maxGrade(grade, 'd');
        console.log('충격/이상음 감지 - d등급 적용');
    }

    if (function_degradation) {
        grade = maxGrade(grade, 'c');
        console.log('기능 저하 감지 - c등급 적용');
    }

    if (aging_or_dirt) {
        grade = maxGrade(grade, 'b');
        console.log('노후화/오염 감지 - b등급 적용');
    }

    if (other_damage) {
        grade = maxGrade(grade, 'b');
        console.log('기타 손상 감지 - b등급 적용');
    }

    console.log('신축이음 상태평가 결과:', grade);
    return grade;
}

// 배수시설 상태평가 함수
function evaluateDrainageFacility(damage_status = '-') {
    /**
     * 배수시설 상태평가 등급(a~d)을 반환하는 함수
     *
     * @param {string} damage_status - 손상현황 문자열
     * @returns {string} 상태평가 등급: 'a', 'b', 'c', 'd'
     */

    console.log('배수시설 상태평가 시작:', { damage_status });

    // 손상이 없는 경우
    if (!damage_status || damage_status === '-' || damage_status === '양호') {
        console.log('손상 없음 - a등급 적용');
        return 'a';
    }

    // 심각한 손상: 파손, 노후화
    if (damage_status.includes('파손') || damage_status.includes('노후')) {
        console.log('파손/노후화 감지 - d등급 적용');
        return 'd';
    }

    // b등급 손상: 배수구 막힘
    // if (damage_status.includes('배수구 막힘')) {
    //     console.log('배수구 막힘 감지 - b등급 적용');
    //     pavementEvaluationTable
    //     return 'b';
    // }

    // c등급 손상: 막힘, 퇴적, 누수, 불량, 부적절, 탈락, 길이부족
    const cGradeKeywords = ['막힘', '퇴적', '누수', '불량', '부적절', '탈락', '길이부족'];
    for (let keyword of cGradeKeywords) {
        if (damage_status.includes(keyword)) {
            console.log(`${keyword} 손상 감지 - c등급 적용`);
            return 'c';
        }
    }

    // 기타 손상이 있는 경우 b등급
    console.log('기타 손상 감지 - b등급 적용');
    return 'b';
}

// 상태등급을 결함도 점수로 변환하는 함수
function grade_to_defect_score(grade) {
    /**
     * 상태등급을 결함도 점수로 변환하는 함수
     *
     * @param {string} grade - 상태등급 (a~e)
     * @returns {number} 결함도 점수
     */
    grade = grade.toLowerCase();
    if (grade === 'a') {
        return 0.1;
    } else if (grade === 'b') {
        return 0.2;
    } else if (grade === 'c') {
        return 0.4;
    } else if (grade === 'd') {
        return 0.7;
    } else if (grade === 'e') {
        return 1.0;
    } else {
        return 0.0;
    }
}

function updatePavementCalculations($row, $cells, newArea) {
    // 포장 테이블 구조: 경간, 부재면적, 포장불량면적율, 등급, 주행성, 등급, 배수구막힘, 배수, 최종등급

    const damageData = extractOriginalDamageValue($cells.eq(2)); // 포장불량 면적율 셀

    console.log(`포장 손상물량 추출:`, {damageData});

    // 포장불량 면적율 계산 및 업데이트
    if (damageData.hasData) {
        const newRatio = calculateAreaRatio(damageData.value, newArea);
        $cells.eq(2).text(newRatio > 0 ? newRatio.toFixed(2) : '-').attr('data-original-value', damageData.value);
        $cells.eq(3).text(evaluateGrade(newRatio));
        console.log(`포장불량 면적율 업데이트: ${newRatio > 0 ? newRatio.toFixed(2) : '-'}%`);
    }
}
