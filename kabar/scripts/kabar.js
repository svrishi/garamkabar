
function process_vote(data) {
  rc = data.retcode;
  id = data.id;
  val = data.value;
  if (rc == 1) {
    window.location.href='/signup';
  }
  else if (rc == 2) {
    $("#voteimgsdisp" + id).hide();
    $("#novoteimgsdisp" + id).show();
    $("#points" + id).text(val);
  }
}

$(document).ready(function() {
  $("a[href*='/vote/up/']").click(function() {
    $.post('/vote/up/', {'id': this.id}, function(data) {
      process_vote(data);
    }, "json");
    return false;
  });

  $("a[href*='/vote/down/']").click(function() {
    $.post('/vote/down/', {'id': this.id}, function(data) {
      process_vote(data);
    }, "json");
    return false;
  });
});
