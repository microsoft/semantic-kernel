//! Procedural macros for Semantic Kernel Rust plugin system
//! 
//! This crate provides procedural macros to simplify the creation of plugins
//! and functions for the Semantic Kernel, automatically generating JSON schemas
//! for function calling and implementing the required traits.

use proc_macro::TokenStream;
use proc_macro2::TokenStream as TokenStream2;
use quote::quote;
use syn::{parse_macro_input, DeriveInput, ItemFn, Attribute, Meta, Lit};

/// Marks a function as a Semantic Kernel function
/// 
/// This macro automatically implements the `KernelFunction` trait for the function,
/// generating JSON schema metadata for function calling.
/// 
/// # Example
/// 
/// ```ignore
/// #[sk_function]
/// #[description("Adds two numbers together")]
/// async fn add(a: f64, b: f64) -> f64 {
///     a + b
/// }
/// ```
#[proc_macro_attribute]
pub fn sk_function(_args: TokenStream, input: TokenStream) -> TokenStream {
    let input_fn = parse_macro_input!(input as ItemFn);
    
    match generate_kernel_function(&input_fn) {
        Ok(output) => output.into(),
        Err(err) => err.to_compile_error().into(),
    }
}

/// Marks a struct as a Semantic Kernel plugin
/// 
/// This macro automatically implements the `KernelPlugin` trait for the struct,
/// discovering all methods marked with `#[sk_function]`.
/// 
/// # Example
/// 
/// ```ignore
/// #[sk_plugin]
/// #[name("MathPlugin")]
/// #[description("Mathematical operations")]
/// struct MathPlugin;
/// 
/// impl MathPlugin {
///     #[sk_function]
///     #[description("Adds two numbers")]
///     async fn add(&self, a: f64, b: f64) -> f64 {
///         a + b
///     }
/// }
/// ```
#[proc_macro_attribute]
pub fn sk_plugin(_args: TokenStream, input: TokenStream) -> TokenStream {
    let input_struct = parse_macro_input!(input as DeriveInput);
    
    match generate_kernel_plugin(&input_struct) {
        Ok(output) => output.into(),
        Err(err) => err.to_compile_error().into(),
    }
}

fn generate_kernel_function(input_fn: &ItemFn) -> syn::Result<TokenStream2> {
    let fn_name = &input_fn.sig.ident;
    let fn_name_str = fn_name.to_string();
    
    // Extract description from attributes
    let description = extract_description(&input_fn.attrs)?;
    
    // Generate parameter schema from function signature
    let _param_schema = generate_parameter_schema(&input_fn.sig)?;
    
    // Create the function implementation
    let original_fn = input_fn;
    
    Ok(quote! {
        #original_fn
        
        // Create a wrapper struct that implements KernelFunction
        pub struct #fn_name;
        
        #[semantic_kernel::async_trait]
        impl semantic_kernel::kernel::KernelFunction for #fn_name {
            fn name(&self) -> &str {
                #fn_name_str
            }
            
            fn description(&self) -> &str {
                #description
            }
            
            async fn invoke(
                &self, 
                _kernel: &semantic_kernel::Kernel, 
                arguments: &std::collections::HashMap<String, String>
            ) -> semantic_kernel::Result<String> {
                // Parse arguments and call the function
                // This is simplified - in a real implementation we'd parse based on the schema
                let result = #fn_name().await;
                Ok(result.to_string())
            }
            
            /// Get JSON schema for function calling
            fn get_json_schema(&self) -> serde_json::Value {
                serde_json::json!({
                    "type": "function",
                    "function": {
                        "name": #fn_name_str,
                        "description": #description,
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                })
            }
        }
    })
}

fn generate_kernel_plugin(input_struct: &DeriveInput) -> syn::Result<TokenStream2> {
    let struct_name = &input_struct.ident;
    let plugin_name = extract_plugin_name(&input_struct.attrs)?.unwrap_or_else(|| struct_name.to_string());
    let description = extract_description(&input_struct.attrs)?;
    
    // In a real implementation, we'd discover all sk_function methods
    // For now, we'll create a basic implementation
    
    Ok(quote! {
        #input_struct
        
        #[semantic_kernel::async_trait]
        impl semantic_kernel::kernel::KernelPlugin for #struct_name {
            fn name(&self) -> &str {
                #plugin_name
            }
            
            fn description(&self) -> &str {
                #description
            }
            
            fn functions(&self) -> Vec<&dyn semantic_kernel::kernel::KernelFunction> {
                // TODO: Discover and return all sk_function methods
                vec![]
            }
        }
    })
}

fn extract_description(attrs: &[Attribute]) -> syn::Result<String> {
    for attr in attrs {
        if attr.path().is_ident("description") {
            if let Meta::List(meta_list) = &attr.meta {
                if let Ok(lit) = meta_list.parse_args::<Lit>() {
                    if let Lit::Str(lit_str) = lit {
                        return Ok(lit_str.value());
                    }
                }
            }
        }
    }
    Ok("No description provided".to_string())
}

fn extract_plugin_name(attrs: &[Attribute]) -> syn::Result<Option<String>> {
    for attr in attrs {
        if attr.path().is_ident("name") {
            if let Meta::List(meta_list) = &attr.meta {
                if let Ok(lit) = meta_list.parse_args::<Lit>() {
                    if let Lit::Str(lit_str) = lit {
                        return Ok(Some(lit_str.value()));
                    }
                }
            }
        }
    }
    Ok(None)
}

fn generate_parameter_schema(_sig: &syn::Signature) -> syn::Result<TokenStream2> {
    // Generate JSON schema for function parameters
    // This is simplified - a real implementation would parse all parameter types
    Ok(quote! {
        // TODO: Generate proper parameter schema
    })
}
