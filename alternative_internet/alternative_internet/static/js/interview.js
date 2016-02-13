

$(document).ready(function(){

    var webrtc = new SimpleWebRTC({
        peerConnectionConfig: { iceServers: [{"url": "stun:redecentralize.net:3478"}]},
        localVideoEl: 'localVideo',
        remoteVideosEl: 'remoteVideo',
        autoRequestMedia: true
    })

    var recorder;

    webrtc.on('videoAdded', function(video, peer){
        recorder = RecordRTC(peer.stream, {
           type: 'video',
           width: 320,
           height: 240
        });
    })


    $('#start-record').click(function(){
        recorder.startRecording()
        return false
    })
    $('#stop-record').click(function(){
        recorder.stopRecording(function(videoURL) {
           window.open(videoURL);
        })
        return false
    })
    $('#save-record').click(function(){
        recorder.save()
        return false
    })

    webrtc.on('readyToCall', function () {
        webrtc.joinRoom('redecentralise', function (err, roomInfo) {
            console.log(err)
            console.log(roomInfo)
        });
    });
})
