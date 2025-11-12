 // 손상 데이터 생성에 필요한 보조 함수들
    function getRandomDamageValue(min, max) {
        return (Math.random() * (max - min) + min).toFixed(2);
    }

saveandreplace = function (target,skipSave  = false) {

    var table = $(target).closest('.card').find('table').get(0);
    var type = "slab"; // 버튼의 data-type 속성 값 가져오기

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
        spanId,
        type: type,
        damageType,
        damageQuantity,
        count,
        unit,
        inspectionArea
      });
    });

    if (skipSave) {
      console.log('저장 건너뜀, 데이터:', damage_list);
      // skipSave가 true일 때는 서버 저장이나 상태평가 재생성을 하지 않음
      return;
    }
    // 교량명(파일명)과 사용자 ID는 실제 값으로 대체
    const filename = bridgeData.id;
    const user_id = window.user_id || 1; // 실제 로그인 정보에서 가져오세요

    if (!filename) {
      alert('교량명을 선택하세요.');
      return;
    }

  if (typeof showLoading === 'function') showLoading('저장 중입니다...');
  $.ajax({
      url: '/api/save_span_damage',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({
        filename: filename,
        user_id: user_id,
        damage_list: damage_list
      }),
      success: function (response) {
        if (typeof hideLoading === 'function') hideLoading();
        if (response.success) {
          showSnackMessage('저장되었습니다.', 'info'); // 저장 완료 알림
          // 실제 저장이 성공했을 때만 상태평가 재생성
          updateSlabEvaluationTable(filename);
        } else {
          showSnackMessage('저장 실패: ' + (response.error || '알 수 없는 오류'));
        }
      },
      error: function () {
        if (typeof hideLoading === 'function') hideLoading();
        showSnackMessage('저장 중 오류가 발생했습니다.');
      }
    });
  }
$(document).ready(function () {
  // 바닥판 상태평가 저장 버튼 클릭 시
  $('button[id^=crackSave]').on('click', function () {

    saveandreplace(this);

});
});





function updateSlabEvaluationTable(selectedFilename, skipLoading = false) {
        $.ajax({
                    url: '/api/get_span_damage',
                    method: 'GET',
                    data: { filename: selectedFilename },
                    success: async function(response) {
                        if (response.success) {
                            console.log('span_damage 데이터:', response.data);
                            //showSnackMessage('데이터가 성공적으로 로드되었습니다.[code 85]');
                            get_span_damage = response.data;

                             if(!skipLoading) showLoadingEvalutionForSaved(skipLoading);
                             else
                              await showLoadingEvalution(skipLoading);

0
                             //alert("데이터가 성공적으로 로드되었습니다.");


                            // TODO: 받아온 데이터를 화면에 반영하는 코드 추가
                            // 예: damageData = response.data; 또는 테이블 렌더링 함수 호출
                        } else {
                            console.error('span_damage 데이터 로드 실패:', response.error);
                        }
                    },
                    error: function(xhr, status, error) {
                        console.error('span_damage 데이터 로드 실패:', error);
                    }
                });

}
