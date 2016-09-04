function setupSubtitlesHandling($form){

    var timeInputs;
    var pattern=/^\s*\d(?:\d)?:\d\d:\d\d(?:[,\.]\d+)?\s*$/

    function checkTime($selector, nullOk){
        var text = $.trim($selector.val());
        if (!text && nullOk) return true;
        if (!pattern.test(text)){
            $selector.focus();
            alertError("Invalid time: "+text);
            return false;
        }
        return true;
    }

    function submitCheck(){
        if (!timeInputs) timeInputs=$('input[type="text"]', $form);
        if (!checkTime($(timeInputs[0]))
            || !checkTime($(timeInputs[1]))
            || !checkTime($(timeInputs[2]), true)
            || !checkTime($(timeInputs[2]), b1===null)){
                return false;
        }
        return true;
    }

    $('button[type="submit"]', $form).click(submitCheck);
}