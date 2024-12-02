
var urlCarrinhoPost = '';
var urlDestinoContinuar = '';
var variacao_id = null;
var quantidade = 0;
$(document).ready(function(){

    $.ajaxSetup({
        headers:
        { 'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content') }
    });

    $("#continuar_comprando").on('click', function(e){

        $('tr[data-quant]').each(function() {
            var $row = $(this);
            quantidade = $row.find('.quantidade').val();
            var quantidadeOriginal = $row.data('quant');
            variacao_id = $row.data('variacaoid');
            urlCarrinhoPost = $(this).data('url');
            urlDestinoContinuar = $(this).attr('url-destino');

            if (quantidade != quantidadeOriginal) {
                $("#dialogModal").show();
            }else{
                $("#dialogModal2").show();
            }   
        });                    
    });

    $("#changeCartQuantity").click(function(){
        
        $.ajax({
            type: "POST",
            dataType: "json",
            url: urlCarrinhoPost,
            data: {
                "variacaoid" : variacao_id,
                "quantidade": quantidade,
                "csrfmiddlewaretoken": $('meta[name="csrf-token"]').attr('content')
            },
            success: function(jsonData) { 
                $("#dialogModal").hide();                
            }
        });
                
    });

    $("#closeDialogModal2").click(function(){
        $("#dialogModal2").hide(); 
    });

    $("#closeDialogModal").click(function(){
        $("#dialogModal").hide();
    });
    

});

