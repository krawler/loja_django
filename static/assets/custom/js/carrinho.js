
var quantidade = 0;

$(document).ready(function(){

    $.ajaxSetup({
        headers:
        { 'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content') }
    });

    $("#continuar_comprando").on('click', function(e){

        url = $(this).data('urldestino');
        $("#changeCartQuantity").data('urldestino', url);
        dialogChangeQuantity();
    });

    function isQuantidadeAlterada(){
        var quantidadeAlterada = false;
        $('tr[data-quant]').each(function() {
            var $row = $(this);
            var quantidadeOriginal = $row.data('quant');
            quantidade  = $row.find('.quantidade').val();            

            if (quantidade != quantidadeOriginal) {
                quantidadeAlterada = true;
                return false; //return false to stop jquey loop
            }
        });
        if(quantidadeAlterada == true)
            return true;
        else
            return false;
    }

    $(".quantidade").change(function(){
        let preco_unitario = $(this).parent().parent().children('td.preco_unitario').html();
        let quantidade = $(this).val();
        preco_unitario = preco_unitario.replace('R$','')
        preco_unitario = parseFloat(preco_unitario);
        quantidade = parseInt(quantidade);
        total_parcial = preco_unitario * quantidade;
        total_parcial = formata_preco(total_parcial);
        $(this).parent().parent().children('td.total_parcial').children('span').html(total_parcial);
    });

    $(".quantidade").blur(function(){
        let total_carrinho = 0;
        let qtd_show_str = 0;
        $('tr[data-quant]').each(function() {
            total_parcial = $(this).children('td.total_parcial').children('span').html();
            total_parcial = total_parcial.replace('R$&nbsp;','').replace('R$','').trim();
            total_carrinho = total_carrinho + parseFloat(total_parcial)  
            qtd_show_str = parseInt($(this).children('td').children('input').val()) + qtd_show_str;
        });
        qtd_show_str = qtd_show_str + 'x';
        $(".total_carrinho").html(formata_preco(total_carrinho));
        $("#qtd_carrinho_nav").children('strong').html(qtd_show_str);
    });

    $("#closeDialogModal2").click(function(){
        $("#dialogModal2").hide(); 
    });

    $("#closeDialogModal").click(function(){
        $("#dialogModal").hide();
    });

    $("#goToStore").click(function(){
        $("#dialogModal2").hide();
    });

    $("#finaliza_compra").click(function(){
        url = $(this).data('urldestino');
        $("#dialogModal").find("button").data('urldestino', url)
        dialogChangeQuantity();
    });

    $("#btnFecharDialog2").on('click', function(){
        $("#dialogModal2").hide();     
    });

    $("#btnFecharDialog").on('click', function(){
        $("#dialogModal").hide();     
    });

    $("#changeCartQuantity").click(function(){
        
        urlDestino = $(this).data('urldestino');
        variacao_id = $(this).data('variacao');
        urlCarrinhoPost = $('#url-post-carrinho').val();
        $("#dialogModal").hide(); 
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
                $('tr[data-quant]').each(function() {
                    var $row = $(this);
                    if(variacao_id  == $row.data('variacaoid'))
                        $row.data('quant', quantidade);
                });
                dialogChangeQuantity(urlDestino)
            }
        });
    });
    
    function dialogChangeQuantity(){
        
        if(isQuantidadeAlterada()){
            $('tr[data-quant]').each(function() {
                var $row    =   $(this);
                var quantidadeOriginal = $row.data('quant');
                var nomeProduto = $row.children('td.nome_produto').children('a').html();
                var urlCarrinhoPost  = $('#url_carrinho_post').val();
                var variacao_id      = $row.data('variacaoid');
                quantidade          = $row.find('.quantidade').val();            
                
                if(quantidade < 1){
                    $("#dialogModal").children('div')
                                    .children('div')
                                    .children('div.modal-body')
                                    .html('Não é possível adicionar produto com quantidade abaixo de 1');
                    $("#dialogModal").show();                
                    return false;
                }

                $("#changeCartQuantity").data("variacao", variacao_id)
                        
                if (quantidade != quantidadeOriginal) {
                    
                    quantidadeAlterada = true;
                    //$("#dialogModal").find('button').attr('data-urldestino', urlDestino)
                    $("#dialogModal").children('div')
                                        .children('div')
                                        .children('div.modal-body')
                                        .html('Tem certeza que deseja alterar a quantidade? do produto ' + nomeProduto + ' de ' + quantidadeOriginal + ' para ' + quantidade)
                    $("#dialogModal").show();
                    return false;
                }
            });      
        }
        if(!isQuantidadeAlterada())
            window.location.href = $("#changeCartQuantity").data('urldestino');
    }

});

