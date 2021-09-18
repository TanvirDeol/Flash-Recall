var correct =0;
var wrong =0;

function checkAns(elem){
    elem.disabled = true;
    document.getElementById(elem.value).style.display = "block";
}
function skipQuestion(elem){
    elem.disabled = true;
    document.getElementById("check-"+elem.value).disabled = true;
}
function mark(elem,res){
    if (res===1)correct++;
    else wrong++;
    document.getElementById("correct-"+elem.value).disabled = true;
    document.getElementById("wrong-"+elem.value).disabled = true;
    document.getElementById("score-board").innerHTML ="Your score was "+correct+" out of "+(correct+wrong)+".";
}
function seeScore(){
    document.getElementById("score-board").style.display = "block";
}

function init(){
    document.getElementById("file-upload-button").style.color = "white";
}
$("#files").change(function() {
    filename = this.files[0].name
    console.log(filename);
  });