var $dialog_imdb_choice;
function showImdbChoice(){

    if (!$dialog_imdb_choice){

        var $dialog_imdb_choice=$('#dialog_imdb_choice').on('shown.bs.modal',function(){
            $year1.focus();
        }).keypress(function(e){
            if(e.which== 13) {
                do_search();
                return false;  
            }
        });
        var $year1=$('input[name="year"]', $dialog_imdb_choice);
        var $year2=$('input[name="year2"]', $dialog_imdb_choice);
        var $results=$('input[name="max"]', $dialog_imdb_choice);
        $('button', $dialog_imdb_choice).click(do_search);
    }
    function do_search(){
        var focus=null;
        $year2.parent().removeClass('has-error');

        var year1=parseInt($.trim($year1.val())) || 0;
        if (year1<=0){
            focus=$year1.parent().addClass('has-error');
        } else {
            $year1.parent().removeClass('has-error');            
        }

        var results = parseInt($.trim($results.val())) || 0;
        if (results <= 0){
            $results.parent().addClass('has-error');
            if (!focus) focus=$results;
        } else {
            $results.parent().removeClass('has-error');
        }
        var year2=$.trim($year2.val());
        if (year2){
            year2 = parseInt(year2) || 0;
            if (year2 <= 0){
                $year2.parent().addClass('has-error');
                if (!focus) focus=$year2;
            }
            if (year1>year2){
                var tmp=year1;
                year1=year2;
                year2=year1;
            }
        } else {
            year2=year1;
        }

        if (focus){
            focus.$focus();
        } else {
            Spinner.show();
            window.location.href='/imdb/'+year1+'-'+year2+'/'+results;
        }
    }

    $dialog_imdb_choice.modal();
}