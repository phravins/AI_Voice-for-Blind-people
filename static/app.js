const micBtn=document.getElementById('micBtn');
const msgInput=document.getElementById('msgInput');
const chatForm=document.getElementById('chatForm');
const pdfInput=document.getElementById('pdfInput');
const homeUpload=document.getElementById('homeUpload');
function startVoice(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){return}
  const r=new SR();
  r.lang='en-US';
  r.interimResults=false;
  r.maxAlternatives=1;
  r.onresult=(e)=>{
    const t=e.results[0][0].transcript;
    msgInput.value=t;
    chatForm.submit();
  };
  r.start();
}
if(micBtn){micBtn.addEventListener('click',startVoice)}
if(pdfInput&&homeUpload){
  pdfInput.addEventListener('change',()=>{ if(pdfInput.files.length>0){ homeUpload.submit(); }});
}
document.querySelectorAll('.action').forEach(btn=>{
  btn.addEventListener('click',()=>{ if(msgInput&&chatForm){ msgInput.value=btn.dataset.msg; chatForm.submit(); }});
});
