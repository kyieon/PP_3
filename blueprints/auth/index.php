<?php
session_start();

// 1. code 파라미터 확인
if (!isset($_GET['code'])) {
    echo "인증 코드가 없습니다.";
    exit;
}

$code = $_GET['code'];

// 2. 토큰 요청
$token_url = "https://oauth2.googleapis.com/token";
$data = [
    'code' => $code,
    'client_id' => $client_id,
    'client_secret' => $client_secret,
    'redirect_uri' => $redirect_uri,
    'grant_type' => 'authorization_code'
];

$options = [
    'http' => [
        'header' => "Content-type: application/x-www-form-urlencoded\r\n",
        'method' => 'POST',
        'content' => http_build_query($data),
    ]
];
$context = stream_context_create($options);
$response = file_get_contents($token_url, false, $context);
if ($response === FALSE) {
    echo "토큰 요청 실패";
    exit;
}
$tokenData = json_decode($response, true);

// 3. 사용자 정보 요청
$access_token = $tokenData['access_token'];
$userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo?access_token=" . $access_token;
$userinfo = file_get_contents($userinfo_url);
$userinfoData = json_decode($userinfo, true);

// 4. 세션 저장 및 리다이렉트
$_SESSION['username'] = $userinfoData['email'];
$_SESSION['google_name'] = $userinfoData['name'];
$_SESSION['google_picture'] = $userinfoData['picture'];

// 원하는 페이지로 이동 (예: 메인 페이지)
header("Location: /");
exit;
