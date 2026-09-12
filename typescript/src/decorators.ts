import { KernelFunctionMetadata } from './types';

const METADATA_KEY = Symbol('kernel_function');

export function kernelFunction(meta: KernelFunctionMetadata = {}) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    (descriptor.value as any)[METADATA_KEY] = meta;
  };
}

export function getKernelFunctionMeta(fn: Function): KernelFunctionMetadata | undefined {
  return (fn as any)[METADATA_KEY];
}
