// 로딩바 표시 함수
function showLoadingBar(targetBtnId) {
  let loadingBar = document.getElementById('loading-bar');
  if (!loadingBar) {
    loadingBar = document.createElement('div');
    loadingBar.id = 'loading-bar';
    loadingBar.style.position = 'fixed';
    loadingBar.style.top = '0';
    loadingBar.style.left = '0';
    loadingBar.style.width = '100vw';
    loadingBar.style.height = '100vh';
    loadingBar.style.background = 'rgba(255,255,255,0.5)';
    loadingBar.style.zIndex = '99999';
    loadingBar.style.display = 'flex';
    loadingBar.style.alignItems = 'center';
    loadingBar.style.justifyContent = 'center';
    let loadingText = '검증 중...';
    if (targetBtnId === 'uploadBtn') {
      loadingText = '업로드 중...';
    }
    loadingBar.innerHTML = `<div style="font-size:2rem; color:#333; background:#fff; border-radius:10px; padding:2rem 3rem; box-shadow:0 2px 8px rgba(0,0,0,0.1);"><i class="fas fa-spinner fa-spin me-2"></i>${loadingText}</div>`;
    document.body.appendChild(loadingBar);
  } else {
    loadingBar.style.display = 'flex';
  }
  // 버튼 비활성화
  if (targetBtnId) {
    const btn = document.getElementById(targetBtnId);
    if (btn) btn.disabled = true;
  }
}

// 로딩바 숨김 함수
function hideLoadingBar(targetBtnId) {
  const loadingBar = document.getElementById('loading-bar');
  if (loadingBar) loadingBar.style.display = 'none';
  // 버튼 활성화
  if (targetBtnId) {
    const btn = document.getElementById(targetBtnId);
    if (btn) btn.disabled = false;
  }
}
// 파일 업로드 및 검증 관련 JavaScript 함수들

// 파일 업로드 폼 제출 시 검증 체크
document.addEventListener('DOMContentLoaded', function() {
  console.log('파일 업로드 스크립트 로드됨');

  const uploadForm = document.getElementById('uploadForm');
  if (uploadForm) {
    uploadForm.addEventListener('submit', function(e) {
      const uploadBtn = document.getElementById('uploadBtn');
      const fileInput = document.getElementById('file');
      const fileId = document.getElementById('file_id').value;

      // 새 파일 업로드인 경우 (편집 모드가 아닌 경우)
      if (!fileId && fileInput.files.length > 0) {
        if (uploadBtn.disabled) {
          e.preventDefault();
          console.log('검증되지 않은 파일 업로드 차단');
          alert('파일 검증을 먼저 수행해주세요.');
          return false;
        }
      }
      // 폼 제출 시 업로드 버튼 비활성화 및 텍스트 변경
      uploadBtn.disabled = true;
      uploadBtn.textContent = '업로드 중...';
      console.log('폼 제출 허용');
    });
  }

  // 파일 선택 시 검증 버튼 활성화
  const fileInput = document.getElementById('file');
  if (fileInput) {
    console.log('파일 입력 요소 발견:', fileInput.id, fileInput.name);
    fileInput.addEventListener('change', function(e) {
      console.log('파일 선택 이벤트 발생:', e.target.files.length);
      const file = e.target.files[0];
      const validateBtn = document.getElementById('validateFileBtn');
      const uploadBtn = document.getElementById('uploadBtn');

      if (file) {
        console.log('선택된 파일:', file.name);
        validateBtn.disabled = false;
        uploadBtn.disabled = true; // 검증 전에는 비활성화
        resetValidation();
      } else {
        console.log('파일 선택 취소');
        validateBtn.disabled = true;
        uploadBtn.disabled = true;
        resetValidation();
      }
    });
  }
});

// 검증 상세 내용을 새 창으로 열기
function openValidationDetailsWindow() {
  console.log('검증 상세 내용 새 창 열기');

  // 창 열기 전에 데이터 확인
  if (!window.currentValidationData) {
    alert('검증 데이터가 없습니다. 다시 검증해주세요.');
    return;
  }

  const detailsWindow = window.open('', 'validationDetails',
    'width=1200,height=800,scrollbars=yes,resizable=yes,location=no,menubar=no,status=no,toolbar=no');

  if (detailsWindow) {
    detailsWindow.document.write(generateValidationDetailsHTML());
    detailsWindow.document.close();
    detailsWindow.focus();
  } else {
    alert('팝업 창이 차단되었습니다. 브라우저 설정을 확인해주세요.');
  }
}

// 검증 상세 내용 HTML 생성
function generateValidationDetailsHTML() {
  const data = window.currentValidationData;

  let html = `
  <!DOCTYPE html>
  <html lang="ko">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>파일 검증 상세 내용</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
      <style>
          body { padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
          .table-responsive { max-height: 600px; overflow-y: auto; border: 1px solid #dee2e6; }
          .table th { position: sticky; top: 0; background:rgb(1, 6, 11); z-index: 10; }
          .error-row { background-color: #f8d7da !important; }
          .error-cell { background-color: #f8d7da !important; color: #721c24 !important; }
          .error-summary { background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
      </style>
  </head>
  <body>
      <div class="container-fluid">
          <h2><i class="fas fa-exclamation-triangle text-danger"></i> 파일 검증 상세 내용</h2>
  `;

  // 기본 오류 표시
  if (data.errors && data.errors.length > 0) {
    html += '<div class="error-summary"><h5 class="text-danger"><i class="fas fa-times-circle"></i> 기본 검증 오류</h5><ul>';
    data.errors.forEach(error => {
      html += `<li class="text-danger">${error}</li>`;
    });
    html += '</ul></div>';
  }

  // validation_details의 전체 오류 표시
  if (data.info.validation_details && data.info.validation_details.errors && data.info.validation_details.errors.length > 0) {
    html += '<div class="error-summary"><h5 class="text-danger"><i class="fas fa-times-circle"></i> 파일 구조 오류</h5><ul>';
    data.info.validation_details.errors.forEach(error => {
      html += `<li class="text-danger">${error}</li>`;
    });
    html += '</ul></div>';
  }

  // 상세 검증 결과 표시 (행별 오류)
  if (data.info.validation_details && data.info.validation_details.error_rows && data.info.validation_details.error_rows.length > 0) {
    html += '<div class="error-summary">';
    html += `<h5 class="text-danger"><i class="fas fa-exclamation-triangle"></i> 행별 검증 오류 (${data.info.validation_details.error_rows.length}개 행)</h5>`;
    html += '<div class="mb-3">';

    data.info.validation_details.error_rows.forEach((errorRow, index) => {
      html += `<div class="card border-danger mb-2">`;
      html += `<div class="card-header bg-danger bg-opacity-10 py-2">`;
      html += `<strong>행 ${errorRow.row_index}번</strong> - ${errorRow.errors.length}개 오류`;
      html += `</div>`;
      html += `<div class="card-body py-2">`;

      // 오류 목록
      html += '<ul class="list-unstyled mb-2">';
      errorRow.errors.forEach(error => {
        html += `<li class="text-danger small"><i class="fas fa-exclamation-circle"></i> ${error}</li>`;
      });
      html += '</ul>';

      // 해당 행 데이터 표시
      html += '<div class="row small text-muted">';
      Object.entries(errorRow.data).forEach(([key, value]) => {
        html += `<div class="col-6 col-md-4"><strong>${key}:</strong> ${value || '(비어있음)'}</div>`;
      });
      html += '</div>';

      html += `</div></div>`;
    });

    html += '</div></div>';
  }
  console.log('상세 검증 결과 표시 완료');
  console.log(data.info.table_preview);
  //alert('테이블 미리보기: ' + (data.info.table_preview ? '있음' : '없음'));
  // 전체 테이블 표시
  if (data.info.table_preview) {
    html += '<h5><i class="fas fa-table"></i> 전체 파일 내용</h5>';
    html += '<div class="table-responsive">';
    html += data.info.table_preview;
    html += '</div>';

    // 범례 추가
    if (data.info.validation_details && data.info.validation_details.error_rows && data.info.validation_details.error_rows.length > 0) {
      html += `
        <div class="alert alert-info mt-3">
          <small>
            <i class="fas fa-info-circle"></i>
            <span style="background-color: #f8d7da; padding: 2px 6px; border: 1px solid #dc3545; border-radius: 3px;">빨간색 배경</span>의 행은 검증 오류가 있는 행입니다.
            마우스를 올려보면 상세 오류 내용을 확인할 수 있습니다.
          </small>
        </div>
      `;
    }
  }

  // 통계 정보
  if (data.info) {
    html += '<h5 class="mt-4"><i class="fas fa-chart-bar"></i> 파일 통계</h5>';
    html += '<div class="row">';
    html += `<div class="col-md-3"><strong>전체 행 수:</strong> ${data.info.total_rows || 0}</div>`;
    html += `<div class="col-md-3"><strong>전체 열 수:</strong> ${data.info.total_columns || 0}</div>`;
    if (data.validation_details) {
      html += `<div class="col-md-3"><strong>유효한 행:</strong> <span class="text-success">${data.validation_details.valid_rows || 0}</span></div>`;
      html += `<div class="col-md-3"><strong>오류 행:</strong> <span class="text-danger">${data.validation_details.error_rows ? data.validation_details.error_rows.length : 0}</span></div>`;
    }
    html += '</div>';
  }

  html += `
      </div>
      <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
  </body>
  </html>
  `;

  return html;
}

// 파일 정보 로드 함수
function populateForm(file) {
  console.log('파일 정보 로드:', file); // 디버깅용 로그
  document.getElementById("file_id").value = file.id || "";
  console.log('파일 ID 설정:', file.id); // ID 디버깅 로그
  document.getElementById("bridge_name").value = file.bridge_name || "";

  // 추가된 필드들을 실제 입력 필드에 설정
  document.getElementById("length").value = file.length || "";
  document.getElementById("width").value = file.width || "";
  document.getElementById("structure_type").value = file.structure_type || "";
  document.getElementById("span_count").value = file.span_count || "";
  document.getElementById("expansion_joint_location").value = file.expansion_joint_location || "";

  // 파일 필드는 선택적으로 만들기 (편집 모드에서는 파일을 다시 선택하지 않아도 됨)
  document.getElementById("file").required = false;

  // 모달 제목 변경
  document.getElementById("uploadModalLabel").textContent = '파일 정보 편집';

  // 모달 표시
  const modal = new bootstrap.Modal(document.getElementById("uploadModal"));
  modal.show();
}

function clearForm() {
  console.log('폼 초기화 시작');
  document.getElementById("uploadForm").reset();
  document.getElementById("file_id").value = "";
  document.getElementById("uploadModalLabel").textContent = '파일 업로드';


  document.getElementById('fileInputContainer').hidden = false;
  document.getElementById('validateFileBtn').style.display = 'block';
  document.getElementById('validationResult').hidden = false;


  // 파일 필드를 필수로 되돌리기
  document.getElementById("file").required = true;

  // 검증 결과 초기화
  resetValidation();

  // 로그 추가
  console.log('폼 초기화 완료');
}

// 검증 결과 초기화
function resetValidation() {
  console.log('검증 결과 초기화');
  const resultDiv = document.getElementById('validationResult');
  const uploadBtn = document.getElementById('uploadBtn');

  resultDiv.style.display = 'none';
  uploadBtn.disabled = true;
}

// 파일 검증 함수
function validateFile() {
  console.log('파일 검증 시작');

  const fileInput = document.getElementById('file');
  const file = fileInput.files[0];

  if (!file) {
    console.log('선택된 파일이 없음');
    alert('파일을 먼저 선택해주세요.');
    return;
  }

  console.log('검증할 파일:', file.name);

  // 로딩 상태 표시
  const validateBtn = document.getElementById('validateFileBtn');
  const originalText = validateBtn.textContent;
  validateBtn.textContent = '검증 중...';
  validateBtn.disabled = true;

  // FormData 생성
  const formData = new FormData();
  formData.append('file', file);

  // AJAX 요청
  fetch('/api/validate_file', {
    method: 'POST',
    body: formData
  })
  .then(async response => {
    console.log('서버 응답 수신:', response.status, response.ok);
    let data;
    try {
      data = await response.json();
    } catch (e) {
      // JSON 파싱 실패 (HTML 등)
      throw new Error('서버에서 올바른 JSON을 반환하지 않았습니다. 상태코드: ' + response.status);
    }
    if (!response.ok) {
      // 서버 오류 메시지가 있으면 표시
      throw new Error(data && data.error ? data.error : 'HTTP 오류: ' + response.status);
    }
    return data;
  })
  .then(data => {
    console.log('검증 결과 데이터:', data);
    console.log('data.success:', data.success);
    console.log('data.is_valid:', data.is_valid);
    console.log('data.errors:', data.errors);

    if (data.success) {
      displayValidationResult(data);
    } else {
      console.log('검증 실패:', data.error);
      showValidationError(data.error || '파일 검증에 실패했습니다.');
    }
  })
  .catch(error => {
    console.error('검증 요청 오류 상세:', error);
    console.error('오류 타입:', error.name);
    console.error('오류 메시지:', error.message);
    console.error('오류 스택:', error.stack);
    showValidationError('파일 검증 중 오류가 발생했습니다: ' + (error && error.message ? error.message : error));
  })
  .finally(() => {
    // 로딩 상태 해제
    validateBtn.textContent = originalText;
    validateBtn.disabled = false;
    hideLoadingBar('validateFileBtn'); // Hide loading bar after validation
  });
}

// 검증 결과 표시
function displayValidationResult(data) {
  console.log('검증 결과 표시:', data);

  // 검증 데이터를 전역 변수에 저장
  window.currentValidationData = data;

  const resultDiv = document.getElementById('validationResult');
  const statusDiv = document.getElementById('validationStatus');
  const detailsDiv = document.getElementById('validationDetails');
  const contentDiv = document.getElementById('validationContent');
  const uploadBtn = document.getElementById('uploadBtn');

  resultDiv.style.display = 'block';

  // 상세 검증 결과가 있는지 체크
  const hasDetailedValidation = data.validation_details && data.validation_details.error_rows;
  const hasValidationErrors = data.validation_details && data.validation_details.errors;

  // 모든 오류 개수 계산
  const totalErrors = (data.errors ? data.errors.length : 0) +
                     (hasDetailedValidation ? data.validation_details.error_rows.length : 0) +
                     (hasValidationErrors ? data.validation_details.errors.length : 0);



  if (data.is_valid && totalErrors === 0) {
    console.log('검증 성공');
    statusDiv.className = 'alert alert-success';
    statusDiv.innerHTML = `
      <i class="fas fa-check-circle"></i> 검증 성공! 파일을 업로드할 수 있습니다.
      <button class="btn btn-sm btn-outline-success ms-2" type="button"
              data-bs-toggle="collapse" data-bs-target="#validationDetails">
        상세 정보 보기
      </button>
    `;
    uploadBtn.disabled = false; // 검증 성공 시 업로드 버튼 활성화
  } else {
    console.log('검증 실패:', totalErrors, '개 오류');
    statusDiv.className = 'alert alert-danger';
    statusDiv.innerHTML = `
      <i class="fas fa-exclamation-triangle"></i> 검증 실패 - ${totalErrors}개의 오류가 발견되었습니다.
      <button class="btn btn-sm btn-outline-danger ms-2" type="button"
              onclick="openValidationDetailsWindow()"
              id="showDetailsBtn">
        오류 내용 보기
      </button>
    `;
    uploadBtn.disabled = true; // 검증 실패 시 업로드 차단

    // 오류가 있으면 상세 내용을 자동으로 펼치기
    setTimeout(() => {
      const collapseElement = document.getElementById('validationDetails');
      if (collapseElement) {
        const bsCollapse = new bootstrap.Collapse(collapseElement, {
          toggle: false
        });
        bsCollapse.show();
      }
    }, 100);
  }

  // 상세 정보 생성
  let detailsHtml = '';

  // 기본 오류 표시 (data.errors) - 가장 먼저 표시
  if (data.errors && data.errors.length > 0) {
    detailsHtml += '<div class="alert alert-danger border-danger mb-3">';
    detailsHtml += '<h6 class="text-danger mb-2"><i class="fas fa-times-circle"></i> 파일 구조 오류</h6>';
    detailsHtml += '<ul class="list-unstyled mb-0">';
    data.errors.forEach(error => {
      detailsHtml += `<li class="text-danger mb-1"><i class="fas fa-exclamation-circle"></i> ${error}</li>`;
    });
    detailsHtml += '</ul></div>';
  }

  // validation_details의 전체 오류 표시
  if (data.validation_details && data.validation_details.errors && data.validation_details.errors.length > 0) {
    detailsHtml += '<div class="alert alert-warning border-warning mb-3">';
    detailsHtml += '<h6 class="text-warning mb-2"><i class="fas fa-exclamation-triangle"></i> 데이터 검증 오류</h6>';
    detailsHtml += '<ul class="list-unstyled mb-0">';
    data.validation_details.errors.forEach(error => {
      detailsHtml += `<li class="text-warning mb-1"><i class="fas fa-exclamation"></i> ${error}</li>`;
    });
    detailsHtml += '</ul></div>';
  }

  // 상세 검증 결과 표시 (행별 오류)
  if (hasDetailedValidation) {
    detailsHtml += generateDetailedValidationDisplay(data.validation_details);
  }

  // 경고 표시
  if (data.warnings && data.warnings.length > 0) {
    detailsHtml += '<h6 class="text-warning"><i class="fas fa-exclamation-triangle"></i> 경고</h6><ul class="list-unstyled mb-3">';
    data.warnings.forEach(warning => {
      detailsHtml += `<li class="text-warning"><i class="fas fa-exclamation"></i> ${warning}</li>`;
    });
    detailsHtml += '</ul>';
  }

  // 파일 정보 표시
  if (data.info) {
    detailsHtml += '<h6 class="text-info"><i class="fas fa-info-circle"></i> 파일 정보</h6>';
    detailsHtml += `<p><strong>전체 행 수:</strong> ${data.info.total_rows || 0}</p>`;
    detailsHtml += `<p><strong>전체 열 수:</strong> ${data.info.total_columns || 0}</p>`;

    if (data.validation_details) {
      detailsHtml += `<p><strong>유효한 행:</strong> <span class="text-success">${data.validation_details.valid_rows || 0}</span></p>`;
      detailsHtml += `<p><strong>오류 행:</strong> <span class="text-danger">${data.validation_details.error_rows ? data.validation_details.error_rows.length : 0}</span></p>`;
    }
  }

  // 테이블 미리보기 표시
  if (data.table_preview) {
    detailsHtml += '<h6 class="text-info mt-4"><i class="fas fa-table"></i> 파일 미리보기</h6>';
    detailsHtml += '<div class="table-responsive" style="max-height: 400px; overflow-y: auto;">';
    detailsHtml += data.table_preview;
    detailsHtml += '</div>';

    // 오류 행 하이라이트 적용
    setTimeout(() => {
      highlightErrorRows(data.validation_details);
    }, 100);
  }

  contentDiv.innerHTML = detailsHtml;
}

// 상세 검증 결과 표시 함수
function generateDetailedValidationDisplay(validationDetails) {
  if (!validationDetails || !validationDetails.error_rows || validationDetails.error_rows.length === 0) {
    return '<h6 class="text-success"><i class="fas fa-check-circle"></i> 상세 검증 통과</h6><p>모든 데이터가 올바르게 입력되었습니다.</p>';
  }

  let html = '<h6 class="text-danger"><i class="fas fa-exclamation-triangle"></i> 상세 검증 오류</h6>';
  html += `<p class="text-danger">총 <strong>${validationDetails.error_rows.length}</strong>개 행에서 오류가 발견되었습니다:</p>`;

  // 오류 행 목록 표시 (최대 10개까지만)
  const displayRows = validationDetails.error_rows.slice(0, 10);
  html += '<div class="mb-3">';

  displayRows.forEach((errorRow, index) => {
    html += `<div class="card border-danger mb-2">`;
    html += `<div class="card-header bg-danger bg-opacity-10 py-2">`;
    html += `<strong>행 ${errorRow.row_index}번</strong> - ${errorRow.errors.length}개 오류`;
    html += `</div>`;
    html += `<div class="card-body py-2">`;

    // 오류 목록
    html += '<ul class="list-unstyled mb-2">';
    errorRow.errors.forEach(error => {
      html += `<li class="text-danger small"><i class="fas fa-exclamation-circle"></i> ${error}</li>`;
    });
    html += '</ul>';

    // 해당 행 데이터 표시
    html += '<div class="row small text-muted">';
    Object.entries(errorRow.data).forEach(([key, value]) => {
      html += `<div class="col-6 col-md-4"><strong>${key}:</strong> ${value || '(비어있음)'}</div>`;
    });
    html += '</div>';

    html += `</div></div>`;
  });

  if (validationDetails.error_rows.length > 10) {
    html += `<p class="text-muted small">... 외 ${validationDetails.error_rows.length - 10}개 행에 추가 오류 있음</p>`;
  }

  html += '</div>';

  return html;
}

// 오류 행 하이라이트 함수
function highlightErrorRows(validationDetails) {
  if (!validationDetails || !validationDetails.error_rows) {
    return;
  }

  console.log('오류 행 하이라이트 적용:', validationDetails.error_rows.length, '개 행');

  // 테이블에서 오류 행을 찾아서 빨간색으로 하이라이트
  const previewTable = document.getElementById('preview-table');
  if (!previewTable) {
    console.log('미리보기 테이블을 찾을 수 없음');
    return;
  }

  const rows = previewTable.querySelectorAll('tbody tr');

  validationDetails.error_rows.forEach(errorRow => {
    // 테이블의 행 번호는 0부터 시작하므로 -1
    const tableRowIndex = errorRow.row_index - 1;

    if (tableRowIndex >= 0 && tableRowIndex < rows.length) {
      const row = rows[tableRowIndex];

      // 행 전체에 오류 스타일 적용
      row.style.backgroundColor = '#ffe6e6';
      row.style.border = '2px solid #dc3545';

      // 각 셀에 오류 표시 추가
      const cells = row.querySelectorAll('td');
      cells.forEach(cell => {
        cell.style.backgroundColor = '#ffe6e6';
        cell.style.color = '#721c24';
        cell.style.fontWeight = 'bold';
      });

      // 툴팁으로 오류 내용 표시
      const errorMessages = errorRow.errors.join('\n');
      row.title = `오류: ${errorMessages}`;

      // 오류 아이콘 추가
      const firstCell = cells[0];
      if (firstCell && !firstCell.querySelector('.error-icon')) {
        const errorIcon = document.createElement('i');
        errorIcon.className = 'fas fa-exclamation-triangle text-danger error-icon me-1';
        errorIcon.title = errorMessages;
        firstCell.insertBefore(errorIcon, firstCell.firstChild);
      }

      console.log(`행 ${errorRow.row_index} 하이라이트 완료:`, errorRow.errors);
    }
  });

  // 범례 추가
  const legendHtml = `
    <div class="alert alert-info mt-2">
      <small>
        <i class="fas fa-info-circle"></i>
        <span style="background-color: #ffe6e6; padding: 2px 6px; border: 1px solid #dc3545;">빨간색 배경</span>의 행은 검증 오류가 있는 행입니다.
        마우스를 올려보면 상세 오류 내용을 확인할 수 있습니다.
      </small>
    </div>
  `;

  const tableContainer = previewTable.parentElement;
  if (tableContainer && !tableContainer.querySelector('.validation-legend')) {
    const legendDiv = document.createElement('div');
    legendDiv.className = 'validation-legend';
    legendDiv.innerHTML = legendHtml;
    tableContainer.appendChild(legendDiv);
  }
}

// 검증 오류 표시
function showValidationError(errorMessage) {
  console.log('검증 오류 표시:', errorMessage);

  const resultDiv = document.getElementById('validationResult');
  const statusDiv = document.getElementById('validationStatus');
  const uploadBtn = document.getElementById('uploadBtn');

  resultDiv.style.display = 'block';
  statusDiv.className = 'alert alert-danger';
  statusDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${errorMessage}`;

  uploadBtn.disabled = true;
}

// 편집 모달 열기 함수
function openEditModal(filename, bridgeName, structureType, spanCount, length, width) {
  console.log('편집 모달 열기:', filename);

  // 편집 폼에 기존 값 설정
  document.getElementById('edit_bridge_name').value = bridgeName || '';
  document.getElementById('edit_structure_type').value = structureType || '';
  document.getElementById('edit_span_count').value = spanCount || '';
  document.getElementById('edit_length').value = length || '';
  document.getElementById('edit_width').value = width || '';
  document.getElementById('edit_filename').value = filename;

  // 편집용 구조형식 옵션 로드
  loadEditStructureTypes(structureType);
}

// 편집용 구조형식 옵션 로드
function loadEditStructureTypes(selectedValue = '') {
  fetch("/api/meta_keyword?meta_id=200078")
    .then((response) => response.json())
    .then((data) => {
      const structureSelect = document.getElementById("edit_structure_type");

      // 기존 옵션 제거 (기본 옵션 제외)
      const options = structureSelect.querySelectorAll("option:not(:first-child)");
      options.forEach((option) => option.remove());

      // API 응답에서 옵션 추가
      if (data && data.keywords) {
        data.keywords.forEach((keyword) => {
          const option = document.createElement("option");
          option.value = keyword.keyword;
          option.textContent = keyword.keyword;

          // 기존 값과 일치하면 선택
          if (keyword.keyword === selectedValue) {
            option.selected = true;
          }

          structureSelect.appendChild(option);
        });
      }

      console.log("편집용 구조형식 옵션 로드 완료");
    })
    .catch((error) => {
      console.error("편집용 구조형식 옵션 로드 실패:", error);
    });
}

// 파일 정보 업데이트 함수
function updateFileInfo() {
  const filename = document.getElementById('edit_filename').value;
  const bridgeName = document.getElementById('edit_bridge_name').value.trim();
  const structureType = document.getElementById('edit_structure_type').value;
  const spanCount = document.getElementById('edit_span_count').value;
  const length = document.getElementById('edit_length').value;
  const width = document.getElementById('edit_width').value;

  // 폼 유효성 검사
  if (!bridgeName) {
    alert('교량명을 입력해주세요.');
    document.getElementById('edit_bridge_name').focus();
    return;
  }

  if (!structureType) {
    alert('구조형식을 선택해주세요.');
    document.getElementById('edit_structure_type').focus();
    return;
  }

  if (!spanCount || spanCount < 1) {
    alert('올바른 경간 수를 입력해주세요.');
    document.getElementById('edit_span_count').focus();
    return;
  }

  if (!length || length <= 0) {
    alert('올바른 연장을 입력해주세요.');
    document.getElementById('edit_length').focus();
    return;
  }

  if (!width || width <= 0) {
    alert('올바른 폭을 입력해주세요.');
    document.getElementById('edit_width').focus();
    return;
  }

  // 확인 대화상자
  if (!confirm('파일 정보를 수정하시겠습니까?')) {
    return;
  }

  const formData = {
    filename: filename,
    bridge_name: bridgeName,
    structure_type: structureType,
    span_count: parseInt(spanCount),
    length: parseFloat(length),
    width: parseFloat(width),
    expansion_joint_location: document.getElementById('edit_expansion_joint_location').value.trim() || ''
  };

  // 로딩 상태 표시
  const updateBtn = document.getElementById('updateBtn');
  const originalText = updateBtn.textContent;
  updateBtn.textContent = '수정 중...';
  updateBtn.disabled = true;

  console.log('파일 정보 수정 요청:', formData);

  // API 호출
  fetch('/api/update_bridge_info', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(formData)
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    console.log('파일 정보 수정 응답:', data);

    if (data.success) {
      alert('파일 정보가 성공적으로 수정되었습니다.');

      // 모달 닫기
      const modal = bootstrap.Modal.getInstance(document.getElementById('editModal'));
      if (modal) {
        modal.hide();
      }

      // 페이지 새로고침으로 업데이트된 정보 반영
      setTimeout(() => {
        location.reload();
      }, 500);

    } else {
      throw new Error(data.error || '알 수 없는 오류가 발생했습니다.');
    }
  })
  .catch(error => {
    console.error('파일 정보 수정 오류:', error);
    alert('파일 정보 수정에 실패했습니다: ' + error.message);
  })
  .finally(() => {
    // 로딩 상태 해제
    updateBtn.textContent = originalText;
    updateBtn.disabled = false;
  });
}

// 편집 폼 초기화 (모달이 닫힐 때)
function clearEditForm() {
  document.getElementById('editForm').reset();
  document.getElementById('edit_filename').value = '';
}

// 모달 이벤트 리스너 추가
document.addEventListener('DOMContentLoaded', function() {
  const editModal = document.getElementById('editModal');
  editModal.addEventListener('hidden.bs.modal', function () {
    clearEditForm();
  });
});
