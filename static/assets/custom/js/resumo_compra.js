
$(document).ready(function(){

    $.ajaxSetup({
        headers:
        { 'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content') }
    });

    $("#closeDialogModal").click(function(){
        $("#dialogModal").hide();
    });

    $(".icone_remover_carrinho").click(function(){
        $("#deleteItemCarrinho").data('url', $(this).data('url'));
        variacao_id = $(this).data("variacao");
        $("#deleteItemCarrinho").attr("variacao", variacao_id);
        $("#dialogModal").show();
    });
    
    //se deseja continuar com a exclusão do item
    $("#deleteItemCarrinho").click(function(){
        
        $("#dialogModal").hide();
        url = $(this).data("url");
        variacao_id = $(this).attr("variacao");
        window.location.href = url;

        $.ajax({
            type: "POST",
            dataType: "json",
            url: url,
            data: {
                "variacaoid" : variacao_id,
                "csrfmiddlewaretoken": $('meta[name="csrf-token"]').attr('content')
            },
            success: function(jsonData) {   
                window.location.reload();        
            }
        });
    });
    
});

